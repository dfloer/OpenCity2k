from collections import namedtuple
from PIL import Image
from utils import parse_uint16, parse_uint32
from os import path

"""
This library implements basic sprite data parsing based on specification found at:
https://github.com/dfloer/SC2k-docs/blob/master/sprite%20data%20spec.md#largedat-smallmeddat-specialdat
"""


def parse_data(raw_file):
    """
    Parses the data file containing bitmaps.
    Works for Win95 version of SMALLMED.DAT, SPECIAL.DAT and LARGE.DAT
    Args:
        raw_file (bytes): Raw datafile to parse.
    Returns:
        A dictionary, where the key is the ID of the tile stored in that segment of the file, and the value being the raw bytes.
    """
    large_metadata = {}
    large_data = {}
    large_metaentry = namedtuple("large_metadata", ["offset", "width", "height"])
    large_entry = namedtuple("large_data", ["offset", "width", "height", "length", "data"])
    entries = parse_uint16(raw_file[0 : 2])
    index = raw_file[2: 2 + entries * 10]  # 10B per entry.
    # Generate the metadata on what's in the rest of the file from the header at the start.
    for idx in range(0, len(index), 10):
        item_id = parse_uint16(index[idx : idx + 2])
        offset = parse_uint32(index[idx + 2 : idx + 6])
        height = parse_uint16(index[idx + 6 : idx + 8])
        width = parse_uint16(index[idx + 8 : idx + 10])
        # For duplicates in the data file, allow them, but give the second a -ve ID for later tracking.
        if item_id in large_metadata.keys():
            item_id *= -1
        large_metadata[item_id] = large_metaentry(offset, width, height)
    # Generate the lengths of each chunk.
    end = len(raw_file)
    offsets = []
    for v in large_metadata.values():
        offsets.extend([v.offset])
    offsets.extend([end])
    lengths = [offsets[x] - offsets[x - 1] for x in range(1, len(large_metadata) + 1)]
    # Combine the metadata together with the data.
    idx = 0
    dupes = [x * -1 for x in large_metadata.keys() if x < 0]
    for k, v in large_metadata.items():
        length = lengths[idx]
        idx += 1
        data = raw_file[v.offset: v.offset + length]
        entry = large_entry(v.offset, v.width, v.height, length, data)
        # Now we need to perform some cleanup on the duplicated entries.
        # In this case, we want the second entries, which have a -'ve id, and if we've got the first, ignore them.
        if k < 0:
            k *= -1
        elif k in dupes:
            continue
        large_data[k] = entry
    return large_data


def split_data(raw_data):
    """
    Takes the raw data, reads the small header at the start and then chunks it up and return the list of the chunks.
    Args:
        raw_data (bytes): Raw bytes
    Returns:
        List of the
    """
    posn = 0
    chunks = []
    while True:
        block_len = raw_data[posn]
        extra = raw_data[posn + 1]
        if extra == 2:
            break
        posn += 2
        block = raw_data[posn : posn + block_len]
        if extra == 1 and block == b'\x02\x02':  # This check seems to be needed for MIFF parsing, which uses a similar pixel structure.
            break
        chunks.append(block)
        posn += block_len
    return chunks


def create_image(all_row_data, height, width):
    """
    Takes a split list, one row per list entry and created a Pillow image array for output.
    More information found at: https://github.com/dfloer/SC2k-docs/blob/master/sprite%20data%20spec.md#sprite-data-structure
    Args:
        all_row_data (list): A list containing all of the rows of data.
        height (int): height, in pixels, of the image.
        width (int): width, in pixels, of the image.
    Returns:
        Pillow image array, ready to be turned into an image.
    """
    img_array = [[-1 for _ in range(width)] for _ in range(height)]
    for row_idx, row_data in enumerate(all_row_data):
        if len(row_data) < 3:  # No line should be this short, so skip.
            continue
        offset = 0
        row_len = len(row_data)
        pixel_idx = 0
        while offset < row_len:
            row_mode = row_data[offset + 1]
            if row_mode == 0:
                offset += 2
            elif row_mode == 2:
                offset += 2
            elif row_mode == 3:
                pixel_idx += row_data[offset]
                offset += 2
            elif row_mode == 4:
                pixel_count = row_data[offset]
                offset += 2
                for x in range(pixel_count):
                    img_array[row_idx][pixel_idx] = row_data[offset]
                    pixel_idx += 1
                    offset += 1
                # Why this check? Because sometimes there's extraneous data we need to skip, and this is detectable as a odd pixel count.
                if pixel_count % 2 != 0:
                    offset += 1
            else:
                print("Row mode not found.")
    return img_array


def parse_palette(pallet_filename):
    """
    Generates a palette from the SC2k (win95 at least) version.
    Tested with PAL_MSTR.BMP, but it should work for the others.
    At some point, it'd be nice if they could return a dict of id: {r, g, b) instead.
    Args:
        pallet_filename (path): path to the pallet file to open.
    Returns:
        Pillow image array containing the pallet.
    """
    image = Image.open(pallet_filename)
    img_rgb = image.convert('RGB')
    img_array = [[-1 for _ in range(16)] for x in range(16)]
    palette_start_line = 17
    palette_start_col = 2
    swatch_width = 6
    swatch_height = 5

    for x in range(16):
        for y in range(16):
            pix_x = palette_start_line + (x * swatch_height)
            pix_y = palette_start_col + (y * swatch_width)
            pixel_colour = img_rgb.getpixel((pix_y, pix_x))
            img_array[y][x] = pixel_colour
    return img_array


def write_palette(palette_array, outfile):
    """
    Write the palette as a 16x16 bitmap. Useful for debugging and information purposes.
    Args:
        palette_array (pillow image array): input pallet to be saves out as an image.
        outfile (str): path to the file to be output, including extension.

    Returns:

    """
    out_img = Image.new('RGB', (16, 16), 0)
    for x in range(16):
        for y in range(16):
            out_img.putpixel((y, x), palette_array[y][x])
    print("Writing palette to:", outfile)
    with open(outfile, 'wb') as f:
        out_img.save(f, format='png')


def draw_image(img_array, height, width, palette, outfile, mode='png', animate=False, dump_raw_frames=False):
    """
    Takes an image array and parses the colour information out of it, looks it up in the palette and then creates a bitmap file.
    Mode can be "bmp" with a white background, or "png" with a transparent background. Defaults to "bmp".
    If animate is True, will also great an animated gif version of that sprite as well as the unanimated version.
    Args:
        img_array (pillow image array): pillow representation of the pixels making up the tile.
        height (int): height, in pixels, of the final image.
        width (int): width, in pixels, of the final image.
        palette (pillow image array): mapping from which colours the pixel specifies to RGB values.
        outfile (str): path to the output file to save.
        mode (str): type of file to save.
        animate (bool): whether or not an animated version of the sprite is created.
        dump_raw_frames (bool): Dump each frame from the animation.
    Returns:
        Nothing, but does save the final image.
    """
    frame_delay = 500  # delay between frames in milliseconds
    max_number_frames = 24  # Longest colour animation sequence is the 12 blue sequence, so this is the most frames we'll need. Why 24? Because we have 2, 4, 8 and 12 possible frame lengths and their LCM is 24.
    flash_delay = 2  # How many frames does each of the two states in the 4 two element flashes last?  Game seems to be at 2x delay.

    # Constants for the animations. These are the orders specific animations increment in. Given as their palette x/y coords.
    # Order is (x, y), that is, column index and then row index.
    anim_grey_blue_short = ((11, 10), (12, 10), (13, 10), (14, 10), (15, 10), (0, 11), (1, 11), (2, 11),)
    anim_grey_black = ((3, 11), (4, 11), (5, 11), (6, 11), (7, 11), (8, 11), (9, 11), (10, 11),)
    anim_grey_blue_long = ((11, 11), (12, 11), (13, 11), (14, 11), (15, 11), (0, 12), (1, 12), (2, 12))
    anim_brown_red_yellow_black = ((3, 12), (4, 12), (5, 12), (6, 12),)
    anim_blue = ((8, 12), (9, 12), (10, 12), (11, 12), (12, 12), (13, 12), (14, 12), (15, 12), (0, 13), (1, 13), (2, 13), (3, 13),)
    anim_grey_brown = ((4, 13), (5, 13), (6, 13), (7, 13), (8, 13), (9, 13), (10, 13), (11, 13),)
    anim_flash_red = ((0, 14), (1, 14))
    anim_flash_yellow = ((2, 14), (3, 14))
    anim_flash_green = ((4, 14), (5, 14))
    anim_flash_blue = ((6, 14), (7, 14))

    anim_list = [anim_grey_blue_short, anim_grey_black, anim_grey_blue_long, anim_brown_red_yellow_black, anim_blue,
                 anim_grey_brown, anim_flash_red, anim_flash_yellow, anim_flash_green, anim_flash_blue]

    anim_list_len = [len(x) for x in anim_list]

    anim_check = []
    for x in anim_list:
        anim_check += x

    # These correspond to holes in the palette. Of them, only (8, 14) appears to show up.
    palette_check = (
    (10, 0), (11, 0), (12, 0), (13, 0), (14, 0), (15, 0), (7, 12), (12, 13), (13, 13), (14, 13), (15, 13), (8, 14),  (9, 14), (10, 14), (11, 14), (12, 14), (13, 14), (14, 14), (15, 14), (0, 15), (1, 15), (2, 15), (3, 15), (4, 15), (5, 15),)
    if mode == 'png':
        out_img = Image.new('RGBA', (width, height), 0)
    else:
        out_img = Image.new('RGB', (width, height), 0)

    # Single frame rendering path.
    for x in range(width):
        for y in range(height):
            idx = img_array[y][x]
            if idx != -1:
                i = idx >> 4
                j = idx & 0x0f
                pixel_colour = palette[j][i]
            else:
                if mode == 'png':
                    pixel_colour = (0xff, 0xff, 0xff, 0x00)
                else:
                    pixel_colour = (0xff, 0xff, 0xff)
            out_img.putpixel((x, y), pixel_colour)
    with open(outfile + "." + mode, 'wb') as f:
        out_img.save(f, format=mode)

    # Multiple frame rendering path.
    frames = []
    anim_idx = 0
    found_anim = False  # Are there animated pixels in this frame?
    temp_message = []
    while animate or dump_raw_frames:
        frame = Image.new('RGBA', (width, height), 0)
        for x in range(width):
            for y in range(height):
                idx = img_array[y][x]  # What colour should we be looking up in our palette?
                if idx != -1:
                    i = idx >> 4
                    j = idx & 0x0f
                    pix_coords = (j, i)
                    if pix_coords in anim_check:
                        found_anim = True
                        new_j, new_i = animation_get_pixel(pix_coords, anim_idx, anim_check, anim_list, anim_list_len, flash_delay)
                        pixel_colour = palette[new_j][new_i]
                    elif pix_coords in palette_check:
                        temp_message = [path.split(outfile)[-1], str(pix_coords)]
                        pixel_colour = palette[j][i]
                    else:
                        pixel_colour = palette[j][i]
                else:
                    pixel_colour = (0xff, 0xff, 0xff, 0x00)
                frame.putpixel((x, y), pixel_colour)
        if not found_anim:  # If we don't have animated pixels in this frame, skip this and move on.
            break
        frames += [frame]
        anim_idx += 1
        if len(frames) == max_number_frames:
            break
    # This is mainly here for debugging purposes, and is used with a sprite points to a hole in the pallet.
    if temp_message != []:
        print(f"Sprite id: {temp_message[0]} uses palette index: { temp_message[1]}.")

    if frames != []:
        # Why frames[0].save and append_images=frames[1:]? Because we need a single frame by default, and then the additional frames from there.
        # Using a blank image at the start just yields a blank initial frame.
        with open(outfile + "." + "gif", 'wb') as f:
            frames[0].save(f, save_all=True, append_images=frames[1:], format="gif", loop=0xffff, duration=frame_delay)
        if dump_raw_frames:
            for idx, fr in enumerate(frames):
                with open(outfile + "-" + str(idx) + "." + "png", 'wb') as f:
                    fr.save(f, format="PNG")


def animation_get_pixel(pix_coords, anim_idx, anim_check, anim_list, anim_list_len, flash_delay):
    """
    Takes the current palette coordinates for a pixel for an animation.
    Args:
        pix_coords (tuple): (x, y) coordinates of the pixel's colour in the pallet.
        anim_idx (int): which frame is this?
        anim_check (list): list of all the coordinates corresponding to an animation.
        anim_list (list): List of the pallet indices for the various colour cycles.
        anim_list_len ([int]): number of items in the anim_list
        flash_delay (int): delay, in milliseconds, between each frame.
    Returns:
        the new pixel coordinates for an animation.
    """
    flash_lists = (6, 7, 8, 9)

    # Short circuit if the anim_idx is 0 because this means the pixel we're already on.
    if anim_idx == 0:
        return pix_coords
    # Find where our value is in the list of all the values together.
    pixel_idx = anim_check.index(pix_coords)
    which_list = 0
    # And then use this large value to figure out which actual animation list contains it
    for list_idx, x in enumerate(anim_list_len):
        if (pixel_idx - x) < 0:
            which_list = list_idx  # Because we've been decrementing pixel_idx, when we hit this case, it'll be pointing at the right list element.
            break
        else:
            pixel_idx -= x  # Each time we rule out a list, we decrement the size of that list.
    anim_pixels = anim_list[which_list]  # Get the list of pixel values we actually want to use.
    new_pix_idx = (pixel_idx + anim_idx) % len(anim_pixels)  # Get the pixel that we should be drawing this frame.

    # Handle the four two colour flashers, that don't change every iteration.
    if which_list in flash_lists:
        delay_period = (anim_idx // flash_delay) % 2  # for a flash_delay of 2, will produce something like 00110011...
        return anim_pixels[new_pix_idx ^ delay_period]
    return anim_pixels[new_pix_idx]  # finally return the coordinates into the palette.
