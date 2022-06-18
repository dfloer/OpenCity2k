import argparse
import sys
from pathlib import Path
from PIL import Image

sys.path.append('..')
import sc2_parse as sc2p
import image_parse as imgp
import image_serialize as imgser


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest="input_file", help=".sc2 or .scn file to open, sc2 used to new scenario creation", metavar="INFILE", required=True)
    parser.add_argument('-o', '--output', dest="output_path", help="Path to save output scenario file to. Don't specify if not creating a new scenario.", metavar="OUTFILE", required=False)
    parser.add_argument('-s', '--save-img', dest="output_image", help="directory to output the PICT image to", metavar="FILE", required=False, default=None)
    parser.add_argument('-n', '--new-img', dest="input_image", help="filename and directory for input image for PICT.", metavar="FILE", required=False, default=None)
    parser.add_argument('-p', '--palette', dest="palette_file", help="palette to load", metavar="FILE", required=False, default=None)
    parser.add_argument('-c', '--conditions', dest="scenario_conditions", help="List of scenario win conditions, None for blank, 17 total", metavar="[item, item, ... item]", required=False, default=[], nargs='+', type=int)
    parser.add_argument('-d', '--desc-text', dest="desc_text", help="Descriptive text", metavar="\"TEXT\"", required=False, default='')
    parser.add_argument('-t', '--text', dest="text", help="Scenario selection screen text", metavar="\"TEXT\"", required=False, default='')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    options = parse_command_line()
    filename = options.input_file
    new_conditions = options.scenario_conditions
    in_img = options.input_image
    out_img = options.output_image
    out_path = options.output_path
    text = options.text
    desc_text = options.desc_text
    palette = options.palette_file
    pal = None
    city = sc2p.City()
    city.create_city_from_file(filename)

    if palette:
        try:
            pal = imgp.parse_palette(palette)
        except Exception as e:
            print(f"Palette file open failed with error: {e}")

    if ".sc2" in filename.lower() or not city.scenario:

        try:
            new_conditions = new_conditions.split(', ')
        except Exception:
            pass
        new_image = None
        try:
            new_image = Image.open(in_img)
        except Exception as e:
            print(f"New image open failed with error: {e}")
        if not new_image:
            pass
        if new_image and new_image.size != (63, 63):
            print("Error: New image must be 63x63 pixels only.")
        elif not new_conditions:
            print("Error: New scenario conditions not given, but in creation mode.")
        elif len(new_conditions) != 17:
            print(f"Error: Not enough scenario conditions given, got {len(new_conditions)} but expecting 17.")
        elif not in_img:
            print("Error: Image needed for scenario image.")
        elif not out_path:
            print("Error: Output path to scenario needed to save new scenario.")
        elif not text and not desc_text:
            print("Error: Scenario selection screen and descriptive text needed for new scenario.")
        elif not palette and pal is None:
            print("Error: Palette file needs to be specified to export image.")
        else:
            city.scenario = sc2p.Scenario()
            city.scenario.scenario_text = text
            city.scenario.scenario_descriptive_text = desc_text
            city.scenario.add_conditions(new_conditions)
            city.scenario.img_to_pict(new_image, pal)
            scenario = city.scenario

            if out_path[-4 : ] != ".scn":
                out_path += ".scn"

            print("Created new scenario with the following:")
            print("------\nText:")
            print(scenario.scenario_text)
            print("------\nDescriptive Text:")
            print(scenario.scenario_descriptive_text)
            print("------\nScenario Conditions:")
            print(scenario.scenario_condition)
            print("------\nScenario Picture:")
            print(f"Converted from: \"{in_img}\"")

            try:
                city.save_city(out_path)
            except Exception as e:
                print(f"New scenario save failed with error: {e}")

            print("------\nNew scenario saved to:")
            print(f"\"{out_path}\"")
    else:
        scenario = city.scenario
        print("Text:")
        print(scenario.scenario_text)
        print("\nDescriptive Text:")
        print(scenario.scenario_descriptive_text)
        print("\nScenario Conditions:")
        print(scenario.scenario_condition)

        if out_img:
            if not pal:
                print("Error: Palette file needs to be specified to export image.")
            else:
                img = scenario.pict_to_img(palette)
                if out_img:
                    fp = Path(out_img) / Path(f"pict_{city.city_name}.png")
                    img.save(fp)
