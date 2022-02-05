from PIL import Image
import image_parse as ip
from utils import serialize_uint8
from math import sqrt


def pict_to_bytes(pixels, old_version=False):
    """
    Converts a pixel array of palette indices to their byte representation.
    Args:
        pixels (list(list(int))): List of lists, with each sublist being a row of data. Values are the index to the palette the game is expecting.
        old_version (bool, optional): Serialize in a compatible way. This may be an old version or needed for certain versions of the game. Defaults to False.
    Returns:
        bytes: Raw bytes to be used for serialization.
    """
    w = len(pixels)
    h = len(pixels[0])
    # It appears that older scenarios had a slightly different structure to PICT.
    # This is to potentially preserve compatibility with whatever version of the game is expecting the PICT to be this way.
    # Essentially there's a border, and ending to each line. Newer scenarios don't seem to care, and just ose 0x00 for all non-image data.
    if old_version:
        border = b'\x01'
        row_end = b'\xFF'
    else:
        border = b'\x00'
        row_end = border

    raw_image = border * (w + 2) + row_end
    for row in pixels:
        # Add the border to the start of a data row.
        raw_image += border
        for p in row:
            raw_image += serialize_uint8(p)
        # Add the border, and row ending, to the end of a data row.
        raw_image += border + row_end
    raw_image += border * (w + 2) + row_end
    return raw_image


def img_to_pict(img, palette):
    """
    Turns a Pillow image into a PICT image. This will remap colours if they're not in the palette.
    Args:
        img (Image): Pillow image. Must be 63x63 and already using the colours from the palette.
        palette (pillow image array): mapping from which colours the pixel specifies to RGB values.
    Returns:
        list of lists of integers, representing the full PICT image, including borders.
    """
    remap = remap_closest_colour(img, palette)
    pixel_list = []
    for x in range(63):
        pixel_list += remap[x * 63 : (x + 1) * 63]
    return pixel_list


def remap_closest_colour(img, palette):
    """
    Remaps an image in an arbitrary RGB palette into the specified palette using a standard closest colour distance formula.
    This is useful to convert an existing image, that may include colours not found in SC2k's default palette.
    This may not always produce pleasing results, so it's probably best to create an image using SC2k's palette explicitly.
    Args:
        c (Image): Pillow image to remap colours for.
        palette (pillow image array): mapping from which colours the pixel specifies to RGB values.
    Returns:
        list(int): List where each entry is the index in the palette to use for the PICT value.
    """
    # Note that the indices that are allowed appear to be 18 to 171.
    # Why? Not entirely sure, but this works.
    allowed_colours = [x for x in range(18, 170)]
    pixels = []
    palette = ip.palette_dict(palette)
    pal_colours = list(palette.values())
    for pixel in img.getdata():
        # Some annoying special cases, for whatever reason.
        if pixel == (0, 0, 0):
            closest_colour = 0
        elif pixel == (127, 127, 127):
            closest_colour = 254
        elif pixel == (255, 255, 255):
            closest_colour = 9
        # If there's an exact match, just use it instead.
        elif pixel in pal_colours:
            closest_colour = pal_colours.index(pixel) - 16
        else:
            r, g, b = pixel
            colour_differences = []
            for pal_idx, colour in palette.items():
                if pal_idx not in allowed_colours:
                    continue
                cr, cg, cb = colour
                # This doesn't always seem like it produces the best results.
                # Perhaps there's a bug here, or maybe it's the wrong algorithm for this.
                diff = sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
                colour_differences += [diff]
            closest_colour = colour_differences.index(min(colour_differences))
            # For whatever reason, the greys from indexes 160 to 170 appear in the PICT palette as 0 to 10.
            if closest_colour >= 160:
                closest_colour -= 160
            closest_colour = (closest_colour - 16)# % 256
        if closest_colour < 0:
            print(closest_colour)
        pixels += [closest_colour]
    return pixels
