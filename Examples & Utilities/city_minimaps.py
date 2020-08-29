import argparse
import sys
from pathlib import Path
from PIL import Image
from copy import deepcopy

sys.path.append('..')
import sc2_parse as sc2p
import image_parse as imgp


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest="input_file", help=".sc2 file top open and generate the report on", metavar="INFILE", required=True)
    parser.add_argument('-o', '--output', dest="output_dir", help="path of directory to put the minimaps in", metavar="OUTDIR", required=True)
    parser.add_argument('-p', '--palette', dest="palette", help="path to palette to load", metavar="PALETTE_PATH", required=True)
    parser.add_argument('-d', '--debug', dest="debug", help="draw debug minimaps", required=False, action="store_true")
    args = parser.parse_args()
    return args


def draw_base_minimap(city, palette, rog=False):
    """
    Draws the base minimap, equivalent to the "Structures" minimap in the game.
    Args:
        city (City): city to create the base minimap from.
        palette (dict): palette to use.
        rog (bool, optional): Is this a Rate Of Growth base map, which draws trees as rubble.
    Returns:
        A Pillow image.
    """
    # Indices into the colour palette.
    colour_palette = {"trees": 52, "buildings": 254, "water": 38, "rubble": 83}
    dirt = [24, 247, 231, 215, 199, 183, 167, 151, 135, 119, 103, 87, 71, 55]
    base_image = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    for coords, tile in city.tilelist.items():
        if tile.building:
            colour = palette[colour_palette["buildings"]]
            if tile.building.building_id in range(0x06, 0x0c + 1):
                colour = palette[colour_palette["trees"]]
                if rog:
                    colour = palette[colour_palette["rubble"]]
            elif tile.building.building_id in range(0x01, 0x05 + 1):
                colour = palette[colour_palette["rubble"]]
        elif tile.is_water or tile.terrain >= 0x10:
            colour = palette[colour_palette["water"]]
        else:
            alt = max(0, min(tile.altitude, len(dirt) - 1))
            colour = palette[dirt[alt]]
        base_image.putpixel(coords, colour)
    return base_image


def draw_zones_minimap(city, palette, base_minimap):
    """
    Draws the zones minimap, equivalent to the "Zones" minimap in the game.
    Args:
        city (City): city to create the base minimap from.
        palette (dict): palette to use.
        base_minimap (Image): existing base minimap to use.
    Returns:
        A Pillow image.
    """
    # Indices into the colour palette.
    colour_palette = {"res": 179, "com": 197, "ind": 35}
    zone_image = deepcopy(base_minimap)
    for coords, tile in city.tilelist.items():
        if tile.zone in (1, 2):
            colour = palette[colour_palette["res"]]
        elif tile.zone in (3, 4):
            colour = palette[colour_palette["com"]]
        elif tile.zone in (5, 6):
            colour = palette[colour_palette["ind"]]
        else:
            continue
        zone_image.putpixel(coords, colour)
    return zone_image


def draw_overlay_minimap(city, palette, base_minimap, overlay="traffic"):
    """
    Draws minimaps that have grey overlays on them. This is the Traffic, Pollution, Land Value, Crime, Police/Fire coverage and population density minimaps.
    Args:
        city (City): city to create the base minimap from.
        palette (dict): palette to use.
        base_minimap (Image): existing base minimap to use.
        overlay (str, optional): One of "traffic", "pollution", "value", "crime", "police", "fire", "density". Defaults to "traffic".
    Returns:
        A Pillow image.
    """
    # Indices into the colour palette.
    gradient_colours = [-1, 201, 217, 233, 249, 10, 26, 42, 58, 74, 90, 106, 122, 138, 154, 170]

    minimap_image = deepcopy(base_minimap)
    # The traffic minimap has the roads drawn onto it.
    if overlay == "traffic":
        minimap_image = draw_network_minimap(city, palette, base_minimap, "roads")
    for coords, tile in city.tilelist.items():
        v = getattr(tile, overlay)
        # Values are just binned to one of 16 colours (15 + transparent).
        colour_idx = gradient_colours[v // 16]
        if colour_idx == -1:
            continue
        colour = palette[colour_idx]
        minimap_image.putpixel(coords, colour)
    return minimap_image


def draw_network_minimap(city, palette, base_minimap, network_type="roads"):
    """
    Draws minimaps of networks. This is the Roads and Rail map from the game, as well as a non-game subway map.
    Args:
        city (City): city to create the base minimap from.
        palette (dict): palette to use.
        base_minimap (Image): existing base minimap to use.
        overlay (str, optional): One of "roads", "rails", "subways". Default to "roads".
    Returns:
        A Pillow image.
    """
    network_ids = {
        "roads": list(range(0x1d, 0x2b + 1)) + list(range(0x3f, 0x46 + 1)) + list(range(0x49, 0x59 + 1)) + list(range(0x5d, 0x6b + 1)),
        "rails": list(range(0x2c, 0x3e + 1)) + list(range(0x45, 0x48 + 1))+ [0x5a, 0x5b] + list(range(0x6c, 0x6f + 1)),
        "subways": list(range(0x6c, 0x6f + 1)),
        "tunnels": list(range(0x3f, 0x42 + 1)),
        }
    network = network_ids[network_type]
    network_image = deepcopy(base_minimap)
    for coords, tile in city.tilelist.items():
        if tile.building:
            if tile.building.building_id in network:
                colour = palette[255]
                network_image.putpixel(coords, colour)
        if network_type == "subways" and tile.underground in list(range(0x01, 0x0f + 1)) + [0x23]:
                colour = palette[255]
                network_image.putpixel(coords, colour)
    return network_image


def draw_utility_minimap(city, palette, base_minimap, utility_type="water"):
    """
    Draws a utility minimap. This is power and water.
    Args:
        city (City): city to create the base minimap from.
        palette (dict): palette to use.
        base_minimap (Image): existing base minimap to use.
        utility_type (str, optional): Either "water" or "power". Defaults to "water".
    Returns:
        A Pillow image.
    """
    lookups = {"power": ["powerable", "powered"], "water": ["piped", "watered"]}
    powerlines = list(range(0x0e, 0x1c + 1)) + [0x43, 0x44, 0x47, 0x48, 0x4f, 0x50, 0x5c]
    pipes = list(range(0x10, 0x20 + 1))
    output_minimap = deepcopy(base_minimap)
    for coords, tile in city.tilelist.items():
        colour = None
        if tile.building and utility_type == "power":
            if getattr(tile.bit_flags, lookups[utility_type][0]):
                colour = palette[209]
                if getattr(tile.bit_flags, lookups[utility_type][1]):
                    colour = palette[35]
            if tile.building.building_id in powerlines:
                colour = palette[255]
        elif utility_type == "water":
            if getattr(tile.bit_flags, lookups[utility_type][0]):
                colour = palette[209]
                if getattr(tile.bit_flags, lookups[utility_type][1]):
                    colour = palette[35]
        if tile.underground in pipes and utility_type == "water":
            colour = palette[255]
        if colour is not None:
            output_minimap.putpixel(coords, colour)
    return output_minimap


def draw_buildings_highlight(city, palette, base_minimap, highlight=[255]):
    """
    Highlights all buildings with IDs listed.
    This is useful for the minimaps that show specific building locations.
    Args:
        city (City): city to create the base minimap from.
        palette (dict): palette to use.
        base_minimap (Image): existing base minimap to use.
        highlight (list, optional): List of building IDs to highlight.. Defaults to [255].
    Returns:
        A Pillow image.
    """
    output_minimap = deepcopy(base_minimap)
    for coords, tile in city.tilelist.items():
        if tile.building:
            if tile.building.building_id in highlight:
                colour = palette[255]
                output_minimap.putpixel(coords, colour)
    return output_minimap


def draw_rate_of_growth(city, palette):
    """
    Draws a rate of growth minimap. Values cetermined by inspecting the game.
    Args:
        city (City): city to create the base minimap from.
        palette (dict): palette to use.
        base_minimap (Image): existing base minimap to use.
    Returns:
        A Pillow image.
    """
    output_minimap = draw_base_minimap(city, palette, rog=True)
    for coords, tile in city.tilelist.items():
        growth = tile.growth
        # Negative growth.
        if growth < 0x7d and growth != 0x00:
            colour = palette[209]
            output_minimap.putpixel(coords, colour)
        # Positive growth.
        elif growth > 0x82 and growth != 0xff:
            colour = palette[52]
            output_minimap.putpixel(coords, colour)
    return output_minimap


def draw_corners(city, palette):
    """
    Map primarily for debugging purposes, draws the zone's corners.
    Args:
        city (City): city to create the base minimap from.
        palette (dict): palette to use.
    Returns:
        A Pillow image.
    """
    output_minimap = Image.new('RGBA', (128, 128), (0, 0, 0, 255))
    colours = {0b1111: (255, 0, 255), 0b0001: (255, 0, 0), 0b0010: (0, 255, 0), 0b0100: (0, 0, 255), 0b1000: (255, 255, 0)}
    for coords, tile in city.tilelist.items():
        v = int(tile.zone_corners, 2)
        if v != 0:
            output_minimap.putpixel(coords, colours[v])
    return output_minimap


def draw_bitflags(city, palette, flag=0):
    """
    Map primarily for debugging purposes, draws bitflags.
    Bit flag is one of: "powerable", "powered", "piped", "watered", "xval", "water", "rotate" or "salt".
    Args:
        city (City): city to create the base minimap from.
        palette (dict): palette to use.
        flag (int, optional): Which of the 8 flags should be highlighted? Default = "rotate".
    Returns:
        A Pillow image.
    """
    output_minimap = Image.new('RGBA', (128, 128), (0, 0, 0, 255))
    for coords, tile in city.tilelist.items():
        v = getattr(tile.bit_flags, map_type)
        if v:
            output_minimap.putpixel(coords, (255, 255, 255))
    return output_minimap



if __name__ == "__main__":
    options = parse_command_line()
    in_filename = options.input_file
    out_path = Path(options.output_dir)
    palette_path = Path(options.palette)
    city = sc2p.City()
    city.create_city_from_file(in_filename)
    palette = imgp.palette_dict(imgp.parse_palette(palette_path))
    debug = options.debug

    base_minimap = draw_base_minimap(city, palette)
    with open(out_path / "structures.png", 'wb') as f:
        base_minimap.save(f, format="png")

    zones_minimap = draw_zones_minimap(city, palette, base_minimap)
    with open(out_path / "zones.png", 'wb') as f:
        zones_minimap.save(f, format="png")

    for net_type in ("roads", "rails", "subways"):
        network_minimap = draw_network_minimap(city, palette, base_minimap, net_type)
        with open(out_path / f"{net_type}.png", 'wb') as f:
            network_minimap.save(f, format="png")

    for map in ("traffic", "pollution", "value", "crime", "police", "fire", "density"):
        minimap = draw_overlay_minimap(city, palette, base_minimap, map)
        with open(out_path / f"{map}.png", 'wb') as f:
            minimap.save(f, format="png")

    for map in ("power", "water"):
        network_minimap = draw_utility_minimap(city, palette, base_minimap, map)
        with open(out_path / f"{map}.png", 'wb') as f:
            network_minimap.save(f, format="png")

    highlighted_buildings = {"fire_stations": 0xd3, "schools": 0xd6, "colleges": 0xd9, "police_stations": 0xd2}
    for k, v in highlighted_buildings.items():
        highlighted_minimap = draw_buildings_highlight(city, palette, base_minimap, [v])
        with open(out_path / f"{k}.png", 'wb') as f:
            highlighted_minimap.save(f, format="png")

    rog_minimap = draw_rate_of_growth(city, palette)
    with open(out_path / "growth_rate.png", 'wb') as f:
        rog_minimap.save(f, format="png")

    # Debug minimaps. Here be dragons.
    if debug:
        corners_minimap = draw_corners(city, palette)
        with open(out_path / "_debug_corners.png", 'wb') as f:
            corners_minimap.save(f, format="png")

        for map_type in ("powerable", "powered", "piped", "watered", "xval", "water", "rotate", "salt"):
            flags_minimap = draw_bitflags(city, palette, map_type)
            with open(out_path / f"_debug_flags-{map_type}.png", 'wb') as f:
                flags_minimap.save(f, format="png")
