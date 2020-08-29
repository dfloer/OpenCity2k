import argparse
import sys

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
    args = parser.parse_args()
    return args


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

    city.save_city(output_file)
