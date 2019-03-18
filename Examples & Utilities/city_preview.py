from PIL import Image
import argparse
import sys
from os import path

sys.path.append('..')
import sc2_parse as sc2p
from Data.buildings import get_size as get_building_size


# Some important tile rendering constants.
width = 32 * 128 + 1000
height = 16 * 128 + 1000
w_offset = width // 2
h_offset = 500
layer_offset = -12


def draw_terrain_layer(city, sprites, groundcover=True, networks=True, zones=True, building_type="full"):
    """
    Creates an array of the tiles for terrain layer, optionally with groundcover (trees).
    Args:
        city (City): city object to draw a terrain layer from.
        sprites (dict): id: Image dictionary of sprites to use.
        groundcover (bool): Whether or not to draw groundcover.
        networks (bool): Whether or not to draw networks (roads/rails/power).
        zones (bool): Whether or not to draw zoned, but unbilt, land.
        building_type (str): One of "none", "type" or "full". None draws no buildings, type draws the building type tiles and full draws the full buildings. Currently only none and full are implemented.
    Returns:
        Dictionary of (x, y): Image objects for compositing, where x, y are pixel coordinates.
    """
    terrain_layer = create_terrain_layer(city, sprites)
    zone_layer = {}
    if zones:
        zone_layer = create_zone_layer(city, sprites)
    groundcover_layer = {}
    if groundcover:
        groundcover_layer = create_groundcover_layer(city, sprites)
    network_layer = {}
    if networks:
        network_layer = create_network_layer(city, sprites)
    building_layer = {}
    if building_type != "none":
        building_layer = create_buildings(city, sprites)
    terrain_layer_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    tilelist = city.tilelist

    # This is the order to render all of the tiles in. It still needs tweaking to get correct.
    render_order = []
    city_size = city.city_size
    # This is diagonal rendering.
    for k in range(city_size * 2):
        for j in range(k + 1):
            i = k - j
            if i < city_size and j < city_size:
                render_order += [(i, j)]
    for k in render_order:
        terrain_tile = terrain_layer[k]
        terrain_image = terrain_tile["image"]
        position = terrain_tile["pixel"]
        # If there's a building here, don't draw the terrain under it.
        building_here = False
        if building_type != "none":
            try:
                building_id = tilelist[k].building.building_id
                if building_id >= 108:
                    building_here = True
            except AttributeError:
                building_here = False
        if not building_here:
            terrain_layer_image.paste(terrain_image, position, terrain_image)
            if k in zone_layer.keys():
                zone = zone_layer[k]
                zone_image = zone["image"]
                zone_position = zone["pixel"]
                terrain_layer_image.paste(zone_image, zone_position, zone_image)
        if k in groundcover_layer.keys():
            cover = groundcover_layer[k]
            groundcover_image = cover["image"]
            groundcover_position = cover["pixel"]
            terrain_layer_image.paste(groundcover_image, groundcover_position, groundcover_image)
        if k in network_layer.keys():
            net = network_layer[k]
            net_image = net["image"]
            net_position = net["pixel"]
            terrain_layer_image.paste(net_image, net_position, net_image)
        if k in building_layer.keys():
            building = building_layer[k]
            building_image = building["image"]
            building_position = building["pixel"]
            terrain_layer_image.paste(building_image, building_position, building_image)
    return terrain_layer_image


def create_buildings(city, sprites):
    """
    Creates the image tiles for the buildings layer. Can either do the whole building, or in the case of building_type being True, use the type tiles to draw the building.
    Note that small parks are treated as groundcover in the game, but they're buildings here.
    Args:
        city (City): city object to draw a terrain layer from.
        sprites (dict): id: Image dictionary of sprites to use.
    Returns:
                Dictionary of (row, col): {"pixel": (x, y), "image": Image} objects for compositing.
    """
    building_sprites = {}
    for k in city.buildings.keys():
        row, col = k
        tile = city.tilelist[(row, col)]
        altitude = tile.altitude
        water_table_level = city.simulator_settings["GlobalSeaLevel"]
        rotate = tile.bit_flags.rotate
        # If the tile doesn't have a building on it, it obviously won't have a building id.
        try:
            building_id = tile.building.building_id
        except AttributeError:
            continue

        if altitude < water_table_level:
            altitude = water_table_level
            if tile.terrain == 0x0D:
                altitude -= 1

        image = sprites[1000 + building_id]
        building_size = get_building_size(building_id)

        # Where did these offsets come from?
        # Well, 17 is the size of one tile and is used throughout this code.
        # 25 is the offset when two tiles are stacked.
        # 32 is the offset when three tiles are stacked.
        # 41 is the offset when four tiles are stacked.
        # Note that floor(17 * 1.5) = 25, but floor(17 * 2) = 34 and floor(17 * 2.5) = 42, so while I thought there was a simple pattern, there wasn't.
        # And it just seemed easier to hardcode the magic numbers rather than figure out exactly what formula was being used.
        if building_size == 2:
            extra = image.size[1] - 25
        elif building_size == 3:
            extra = image.size[1] - 32
        elif building_size == 4:
            extra = image.size[1] - 41
        else:  # building_size == 1
            extra = image.size[1] - 17
        shift = altitude * layer_offset
        if rotate:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        i = (row * 16 - col * 16) + w_offset
        j = (row * 8 + col * 8) + h_offset + shift - extra
        building_sprites[(row, col)] = {"pixel": (i, j), "image": image}
    return building_sprites


def create_zone_layer(city, sprites):
    """
    Creates the image tiles for the zone layer.
    Args:
        city (City): city object to draw a terrain layer from.
        sprites (dict): id: Image dictionary of sprites to use.
    Returns:
        Dictionary of (row, col): {"pixel": (x, y), "image": Image} objects for compositing.
    """
    zone_sprites = {}
    for key, tile in city.tilelist.items():
        row, col = key
        tile = city.tilelist[(row, col)]
        altitude = tile.altitude
        zone = tile.zone
        if zone:
            image = sprites[1290 + zone]
            shift = altitude * layer_offset
            i = (row * 16 - col * 16) + w_offset
            j = (row * 8 + col * 8) + h_offset + shift
            zone_sprites[(row, col)] = {"pixel": (i, j), "image": image}
    return zone_sprites


def create_terrain_layer(city, sprites):
    """
    Creates the image tiles for terrain layer.
    Args:
        city (City): city object to draw a terrain layer from.
        sprites (dict): id: Image dictionary of sprites to use.
    Returns:
                Dictionary of (row, col): {"pixel": (x, y), "image": Image} objects for compositing.
    """
    terrain_sprites = {}
    for key, tile in city.tilelist.items():
        row, col = key
        altitude = tile.altitude
        terrain = tile.terrain
        water_table_level = city.simulator_settings["GlobalSeaLevel"]
        is_water = tile.is_water
        tile_id = terrain_to_id(terrain, is_water)

        # If the tile doesn't have a building on it, it obviously won't have a building id.
        try:
            building_id = tile.building.building_id
        except AttributeError:
            building_id = 0

        if altitude < water_table_level:
            altitude = water_table_level
            if tile.terrain == 0x0D:
                altitude -= 1

        image = sprites[1000 + tile_id]
        extra = image.size[1] - 17
        shift = altitude * layer_offset
        # Waterfalls shouldn't draw if there's a dam.
        if tile_id == 284 and building_id in [0xc6, 0xc7]:
            shift = (altitude - 1) * layer_offset + 3
            image = Image.new('RGBA', (1, 1), (0, 0, 0, 0))

        i = (row * 16 - col * 16) + w_offset
        j = (row * 8 + col * 8) + h_offset + shift - extra
        terrain_sprites[(row, col)] = {"pixel": (i, j), "image": image}
    return terrain_sprites


def create_groundcover_layer(city, sprites):
    """
    Creates the image tiles for the groundcover layer.
    Args:
        city (City): city object to draw a terrain layer from.
        sprites (dict): id: Image dictionary of sprites to use.
    Returns:
        Dictionary of (row, col): {"pixel": (x, y), "image": Image} objects for compositing.
    """
    groundcover_sprites = {}
    for k in city.groundcover.keys():
        row, col = k
        tile = city.tilelist[k]
        building = city.groundcover[k]
        altitude = city.tilelist[k].altitude
        terrain = tile.terrain
        water_table_level = city.simulator_settings["GlobalSeaLevel"]
        if altitude < water_table_level:
            altitude = water_table_level
        building_id = building.building_id
        if building_id == 0:
            continue
        image = sprites[1000 + building_id]

        extra = image.size[1] - 17
        shift = altitude * layer_offset
        # Special handling for the 1x1x1 cube terrain piece.
        if terrain == 0x0D:
            shift += layer_offset

        i = (row * 16 - col * 16) + w_offset
        j = (row * 8 + col * 8) + h_offset + shift - extra
        groundcover_sprites[(row, col)] = {"pixel": (i, j), "image": image}
    return groundcover_sprites


def create_network_layer(city, sprites):
    """
    Creates the image tiles for the network (power/rail/roads) layer.
    Args:
        city (City): city object to draw a terrain layer from.
        sprites (dict): id: Image dictionary of sprites to use.
    Returns:
        Dictionary of (row, col): {"pixel": (x, y), "image": Image} objects for compositing.
    """
    network_sprites = {}
    for k in city.networks.keys():
        row, col = k
        tile = city.tilelist[k]
        building = city.networks[k]
        altitude = city.tilelist[k].altitude
        terrain = tile.terrain
        water_table_level = city.simulator_settings["GlobalSeaLevel"]
        rotate = tile.bit_flags.rotate
        if altitude < water_table_level:
            altitude = water_table_level
        building_id = building.building_id
        if building_id == 0:
            continue
        image = sprites[1000 + building_id]

        extra = image.size[1] - 17
        shift = altitude * layer_offset
        if terrain == 0x0D:
            shift += layer_offset

        if rotate:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        i = (row * 16 - col * 16) + w_offset
        j = (row * 8 + col * 8) + h_offset + shift - extra
        network_sprites[(row, col)] = {"pixel": (i, j), "image": image}
    return network_sprites


def render_city_image(input_sc2_path, output_path, sprites_path, city=False, transprent_bg=False):
    """
    Creates a PNG preview of the given city file
    Args:
        input_sc2_path (str): optional path to the input file. Either this or a city object needs to be used, and a city object will override this.
        output_path (str): output path for the preview file to save out.
        sprites_path (str): path to the sprites directory to use to draw the city.
        city (City): city object to render.
        transprent_bg (bool): Whether or not to have a transparent background or not.
    Returns:
        Nothing, but saves a PNG file to disk.
    """
    if not city:
        city = sc2p.City()
        city.create_city_from_file(input_sc2_path)
    sprites = load_sprites(sprites_path)
    if not transprent_bg:
        background = Image.new('RGBA', (width, height), (55, 23, 0, 255))
    else:
        background = Image.new('RGBA', (width, height), (0, 0, 0, 0))

    terrain_layer = draw_terrain_layer(city, sprites, True, True, True, "full")

    background.paste(terrain_layer, (0, 0), terrain_layer)

    with open(output_path + ".png", 'wb') as f:
        background.save(f, format='png')


def load_sprites(sprites_path):
    """
    Loads the sprites into memory.
    Args:
        sprites_path (str): path to the sprites director to open.
    Returns:
        A dictionary containing the sprites.
        Form is {sprite_id: sprite} with the sprite being a Pillow ImageArray.
    """
    sprite_dict = {}
    for sprite_id in range(1001, 1500):
        sprite_path = path.join(sprites_path, str(sprite_id) + ".png")
        sprite_dict[sprite_id] = Image.open(sprite_path)
    return sprite_dict


def terrain_to_id(terrain, is_water):
    """
    Converts an XTER id to the sprite file we need to load.
    Args:
        terrain (int): xter value
        is_water (bool): is this tile covered in water?
    Returns:
        An integer corresponding to the sprite id to use.
    """
    ground = range(0, 0xf)
    underwater = range(0x10, 0x1f)
    shoreline = range(0x20, 0x2f)
    surface_water = range(0x30, 0x3f)
    more_surface_water = range(0x40, 0x46)
    tile_id = 256
    if terrain in ground:
        tile_id = 256 + terrain
    elif terrain in shoreline:
        tile_id = 256 + terrain - 18
    elif terrain in surface_water:
        tile_id = 256 + terrain - 34
    elif terrain in more_surface_water:
        tile_id = 256 + terrain - 35
    elif is_water or terrain in underwater:
        tile_id = 270
    return tile_id


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest="input_file", help="input city filename", metavar="FILE", required=True)
    parser.add_argument('-o', '--output', dest="output_file", help="output image filename", metavar="FILE", required=True)
    parser.add_argument('-s', '--sprites', dest="sprites_dir", help="directory containing sprites", metavar="FILE", required=True)
    parser.add_argument('-t', '--transparent', dest="transparent_bg", help="make image background tranparent", required=False, action="store_true", default=False)
    args = parser.parse_args()
    return args


if __name__ == "__main__":

    options = parse_command_line()
    input_file = options.input_file
    output_file = options.output_file
    image_location = options.sprites_dir
    transparent_bg = options.transparent_bg
    render_city_image(input_file, output_file, image_location, None, transparent_bg)
