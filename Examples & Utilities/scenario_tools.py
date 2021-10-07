import argparse
import sys

sys.path.append('..')
import sc2_parse as sc2p


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest="input_file", help=".scn file top open and generate the report on", metavar="INFILE", required=True)
    # parser.add_argument('-o', '--output', dest="output_file", help="directory to output the images to", metavar="FILE", required=True)
    parser.add_argument('-p', '--palette', dest="palette_file", help="palette to load", metavar="FILE", required=True)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    options = parse_command_line()
    filename = options.input_file
    city = sc2p.City()
    city.create_city_from_file(filename)
    scenario = city.scenario
    print(scenario.scenario_text)
    print(scenario.scenario_descriptive_text)
    print(scenario.scenario_condition)
    # print(scenario.scenario_pict)
    img = scenario.pict_to_img(options.palette_file)
    img.save(f"pict_{city.city_name}.png")