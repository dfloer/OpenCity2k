from PIL import Image
import image_parse as ip
from utils import serialize_uint8
from math import sqrt

def rgb_to_pict(image, palette, exact=True):
    # w = len(image)
    # h = len(image[0])
    img_array = []
    print(image)
    for row in image:
        for col in row:
            img_array += [rgb_to_palette(col, palette)]
    print("img_array", img_array)
    return pict_to_bytes(img_array)


def pict_to_bytes(pixels):
    w = len(pixels)
    h = len(pixels[0])
    # raw_image = b'\x00' * w
    raw_image = b''
    for row in pixels:
        # raw_image += b'\x00'
        for p in row:
            raw_image += serialize_uint8(p)
        raw_image += b'\x00'
    # raw_image += b'\x00' * w
    return raw_image

def rgb_to_palette(rgb, palette):
    for x in palette:
        for y in x:
            if y == rgb:
                return x * 16 + y
    return None


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
    pixel_list = [0 for _ in range(65)]
    for x in range(63):
        pixel_list += [0] + remap[x * 63 : (x + 1) * 63] + [0]
    pixel_list += [0 for _ in range(65)]
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
    # Note that the indices that are allowed appear to be 16 to 171.
    # Which is why there is the -16 offset later in the code.
    # Why? Not entirely sure, but this works.
    allowed_colours = [x for x in range(0, 160)]
    pixels = []
    palette = ip.palette_dict(palette)
    pal_colours = list(palette.values())
    for pixel in img.getdata():
        # If there's an exact match, just use it instead.
        if pixel in palette.values():
            closest_colour = pal_colours.index(pixel)
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
        closest_colour = (closest_colour - 16)
        if closest_colour < 0:
            closest_colour = 0
        # Reverse of the tweak that seemes needed.
        if pixel == (0, 0, 0):
            closest_colour == 0
        elif pixel == (127, 127, 127):
            closest_colour == 254
        pixels += [closest_colour]
    return pixels
