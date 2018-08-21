import argparse
import sys
import os
sys.path.append('..')
from utils import open_file
import image_parse


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest="input_file", help="directory containing large.dat, smallmed.dat and special.dat", metavar="FILE", required=True)
    parser.add_argument('-o', '--output', dest="output_file", help="output location, all in one dir", metavar="FILE", required=True)
    parser.add_argument('-p', '--palette', dest="palette_file", help="palette to load.", metavar="FILE", required=True)
    parser.add_argument('-w', '--write-palette', dest="palette_write", help="location to output palette.png", metavar="FILE", required=False)
    parser.add_argument('-a', '--anim', dest="animate", help="switch to create animated gifs of animated sprites", required=False, default=False, nargs='?')
    parser.add_argument('-d', '--dump', dest="dump_raw_frames", help="switch dump the raw frames", required=False, default=False, nargs='?')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    options = parse_command_line()
    input_path = options.input_file
    output = options.output_file
    files = ["LARGE.DAT", "SMALLMED.DAT", "SPECIAL.DAT"]
    palette_filename = options.palette_file
    animate = options.animate
    dump_raw_frames = options.dump_raw_frames
    if animate is None:
        animate = True
    if dump_raw_frames is None:
        dump_raw_frames = True
    try:
        palette = image_parse.parse_palette(palette_filename)
        if options.palette_write:
            try:
                image_parse.write_palette(palette, "palette.bmp")
            except Exception as e:
                print(f"Writing palette failed with error:\n{e}")
        else:
            try:
                all_files = [open_file(os.path.join(input_path, x)) for x in files]
                for raw_file in all_files:
                    parsed_file = image_parse.parse_data(raw_file)
                    try:
                        for k, v in parsed_file.items():
                            result = image_parse.split_data(v.data)
                            img = image_parse.create_image(result, v.height, v.width)
                            output_path = os.path.join(output, str(k))
                            image_parse.draw_image(img, v.height, v.width, palette, output_path, mode='png', animate=animate, dump_raw_frames=dump_raw_frames)
                    except Exception as e:
                        print(f"Writing sprite ({k}) failed with error:\n{e}")
                        raise
            except Exception as e:
                print(f"Data file opening failed with error:\n {e}")
    except Exception as e:
        print(f"Palette opening failed with error:\n{e}")
