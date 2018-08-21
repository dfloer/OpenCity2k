import argparse
import sys

sys.path.append('..')
import tileset_parse
import image_parse


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest="input_file", help="the .mif file to open", metavar="FILE",
                        required=True)
    parser.add_argument('-o', '--output', dest="output_file", help="directory to output the images to", metavar="FILE",
                        required=True)
    parser.add_argument('-p', '--palette', dest="palette_file", help="palette to load", metavar="FILE",
                        required=True)
    parser.add_argument('-a', '--animate', dest="animate", help="create animated gifs of animated sprites", required=False, default=False, nargs='?')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    options = parse_command_line()
    input_file = options.input_file
    output_file = options.output_file
    animated = options.animate
    if animated is None:
        animated = True
    try:
        palette = image_parse.parse_palette(options.palette_file)
    except Exception as e:
        print("Palette opening failed with error:\n" + str(e))
        raise
    try:
        uncompressed_mif = tileset_parse.open_and_uncompress_mif_file(input_file)
    except Exception as e:
        print("MIF opening failed with error:\n" + str(e))
        raise
    shapes = tileset_parse.parse_miff(uncompressed_mif)
    for shape in shapes:
        try:
            shape.create_sprite(output_file, palette, 'png', animated)
        except Exception as e:
            print("Failed to write sprite with error:\n" + str(e))
            raise
