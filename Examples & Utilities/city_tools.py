import argparse
import sys
from copy import copy

sys.path.append('..')
import sc2_parse as sc2p


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest="input_file", help="input city filename", metavar="FILE", required=True)
    parser.add_argument('-o', '--output', dest="output_file", help="output image filename", metavar="FILE", required=True)
    parser.add_argument('-m', '--money', dest="money", help="amount of money", metavar="NUMBER", required=False)
    parser.add_argument('-t', '--terrain', dest="terrain_mode", help="go into terrain edit mode", required=False, action="store_true")
    parser.add_argument('-p', '--pause', dest="game_pause", help="pause the game", required=False, action="store_true")
    parser.add_argument('-n', '--no-sound', dest="mute", help="mute music and fx", required=False, action="store_true")
    parser.add_argument('--fix-offset', dest="fix_offset", help="fix  cursor offset from terrain", required=False, action="store_true")
    args = parser.parse_args()
    return args


def remove_water_depth_land(city):
    """
    This one requires some explanation, but it seems in certain cases SC2k's terrain editor gets out of sync with the actual state.
    This leads to a situation where raising or lowering terrain makes the cursor get offset from the actual screen position.
    This _seems_ to be due to the water depth being set incorrectly in places without water.
    This function clamps the water depth to the altitude when the tile isn't covered in water, as a fix.
    Args:
        city (City): city to edit.
    """
    for tile in city.tilelist.values():
        if tile.is_water:
            tile.water_depth = tile.altitude

if __name__ == "__main__":
    options = parse_command_line()
    input_file = options.input_file
    output_file = options.output_file
    money = options.money
    terrain_mode = options.terrain_mode
    mute = options.mute

    city = sc2p.City()
    city.create_city_from_file(input_file)

    if money:
        city.city_attributes["TotalFunds"] = min(int(money), 2 ** 31 - 1)
    if terrain_mode:
        city.simulator_settings["GameMode"] = 0
    if options.game_pause:
        city.game_settings["GameSpeed"] = 1
    if options.mute:
        city.game_settings["UserSoundOn"] = 0
        city.game_settings["UserMusicOn"] = 0
    if options.fix_offset:
        remove_water_depth_land(city)

    city.save_city(output_file)
