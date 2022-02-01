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
    Turns a Pillow image into a PICT image.
    Args:
        img (Image): Pillow image. Must be 63x63 and already using the colours from the palette.
        palette (pillow image array): mapping from which colours the pixel specifies to RGB values.
    Returns:
        list of lists of integers, representing the full PICT image, including borders.
    """
    raw_img = list(img.getdata())
    pict_img = [[0] * 65]
    for x in range(0, len(raw_img), 63):
        r = [0]
        for p in raw_img[x : x + 63]:
            for a in range(16):
                for b in range(16):
                    if p == palette[a][b]:
                        r += [a * 16 + b]
        #             else:
        #                 print("potat")
        # r += [0]
        pict_img += r
    pict_img = [[0] * 65]
    return pict_img


def img_to_pict_2(img, palette):
    """
    Turns a Pillow image into a PICT image. Attempt 2, with remapping.
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
    print(len(remap), len(pixel_list))
    print(63 * 63, 65 * 65)
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
    pixels = []
    palette = ip.palette_dict(palette)
    for pixel in img.getdata():
        r, g, b = pixel
        colour_differences = []
        for pal_idx, colour in palette.items():
            if pal_idx > 160:  # The cycling colours aren't used, and shouldn't be checked.
                break
            cr, cg, cb = colour
            diff = sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
            colour_differences += [diff]
        closest_colour = colour_differences.index(min(colour_differences))
        pixels += [closest_colour]
    return pixels
