import argparse
import sys
from pathlib import Path
from PIL import Image

sys.path.append('..')
import sc2_parse as sc2p
import image_parse as imgp

def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest="input_file", help=".sc2 file top open and generate the report on", metavar="INFILE", required=True)
    parser.add_argument('-o', '--output', dest="output_dir", help="path of directory to put the minimaps in", metavar="OUTDIR", required=True)
    parser.add_argument('-p', '--palette', dest="palette", help="path to palette to load", metavar="PALETTE_PATH", required=True)
    args = parser.parse_args()
    return args



def draw_base_minimap(city, palette):
    """
    Draws the base minimap, equivalent to the "Structures" minimap in the game.
    Args:
        city (City): city to create the base minimap from.
        palette (dict): palette to use.
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
            if tile.building.building_id in range(0x06, 0x0c):
                colour = palette[colour_palette["trees"]]
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
    zone_image = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
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
    base_minimap.paste(zone_image, (0, 0), zone_image)
    return base_minimap

if __name__ == "__main__":
    options = parse_command_line()
    in_filename = options.input_file
    out_path = Path(options.output_dir)
    palette_path = Path(options.palette)
    city = sc2p.City()
    city.create_city_from_file(in_filename)
    palette = imgp.palette_dict(imgp.parse_palette(palette_path))

    base_minimap = draw_base_minimap(city, palette)
    with open(out_path / "structures.png", 'wb') as f:
        base_minimap.save(f, format="png")

    zones_minimap = draw_zones_minimap(city, palette, base_minimap)
    with open(out_path / "zones.png", 'wb') as f:
        zones_minimap.save(f, format="png")
