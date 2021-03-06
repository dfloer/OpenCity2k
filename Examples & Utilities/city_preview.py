from PIL import Image
import argparse
import sys
from os import path
import random

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
    things_layer = create_things_layer(city, sprites)
    disaster_layer = create_disaster_layer(city, sprites)
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
        # Draw the edge if we're on the edge of the map.
        if k[0] == 127 or k[1] == 127:
            edge_stack = draw_edge(city, sprites, k)[k]
            edge_image = edge_stack["image"]
            edge_position = edge_stack["pixel"]
            terrain_layer_image.paste(edge_image, edge_position, edge_image)
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
        if k in disaster_layer.keys():
            disaster = disaster_layer[k]
            disaster_image = disaster["image"]
            disaster_position = disaster["pixel"]
            terrain_layer_image.paste(disaster_image, disaster_position, disaster_image)
        if k in things_layer.keys():
            thing = things_layer[k]
            thing_image = thing["image"]
            thing_position = thing["pixel"]
            terrain_layer_image.paste(thing_image, thing_position, thing_image)
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
    # Not all buildings should be rotated when the sprites are rotated on map rotation.
    # Notably highway pieces.
    do_not_rotate_ids = list(range(0x49, 0x50 + 1)) + list(range(0x61, 0x69 + 1))
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
        # This can happen with magic erased buildings, and we shouldn't attempt to draw them.
        if building_id == 0:
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
        # On two of the rotation settings, sprites are flipped.
        if city.simulator_settings["Compass"] in (1, 3) and building_id not in do_not_rotate_ids:
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
        if tile.bit_flags.rotate:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
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
    traffic_tiles = {29: 400, 30: 401, 31: 402, 32: 403, 33: 404, 34: 405, 35: 406, 36: 407, 37: 408, 38: 409, 39: 401,
                     40: 400, 41: 401, 42: 400, 43: 401, 67: 400, 68: 401, 69: 400, 70: 401, 73: 410, 74: 411, 75: 410,
                     76: 411, 77: 410, 78: 411, 79: 410, 80: 411, 93: 414, 94: 415, 95: 416, 96: 417, 97: 418, 98: 419,
                     99: 420, 100: 421, 101: 422, 102: 423, 103: 424, 104: 425, 105: 426}
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
        image = sprites[1000 + building_id].copy()

        extra = image.size[1] - 17
        shift = altitude * layer_offset
        if terrain == 0x0D:
            shift += layer_offset
        if building_id in traffic_tiles.keys():
            traffic_image = get_traffic_image(tile, city.networks, sprites)
            if traffic_image:
                traffic_image_offset = image.size[1] - traffic_image.size[1]
                # This extra mask generation step is so that traffic doesn't draw on top of power lines, railroad tracks and crosswalks.
                # There's probably a better way of doing this, but it works for now.
                mask = Image.new('RGBA', (traffic_image.size), (0, 0, 0, 0))
                w, h = traffic_image.size
                for x in range(w):
                    for y in range(h):
                        p = traffic_image.getpixel((x, y))
                        base_p = image.getpixel((x, y))
                        # We only want to draw if we're a car (blue or black), but only on something road coloured.
                        # Yes, this means that the cars draw *under* the crosswalk and traintracks, but it's this was in the original game.
                        # Possible tweak here is to only not draw when base_p is not (0, 0, 0, 255) (black).
                        if p != (140, 140, 140, 255) and base_p == (143, 143, 143, 255):
                            mask.putpixel((x, y), p)
                image.paste(traffic_image, (0, traffic_image_offset), mask)
        if rotate:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        r, c = building.tile_coords
        i = (r * 16 - c * 16) + w_offset
        j = (r * 8 + c * 8) + h_offset + shift - extra
        network_sprites[(r, c)] = {"pixel": (i, j), "image": image}
    return network_sprites


def get_traffic_image(tile, networks, sprites):
    """
    Gets the traffic image for a certain tile.
    Traffic threshold values pulled from the game. First value is from (visually) no traffic to normal traffic, and the second is the traffic value to go from normal traffic to heavy traffic.
    Args:
        tile (Tile): tile to get the traffic image for.
        sprites (dict): id: Image dictionary of sprites to use.
    Returns:
        Image with the traffic overlay.
    """
    traffic_tiles = {29: 400, 30: 401, 31: 402, 32: 403, 33: 404, 34: 405, 35: 406, 36: 407, 37: 408, 38: 409, 39: 401,
                     40: 400, 41: 401, 42: 400, 43: 401, 67: 400, 68: 401, 69: 400, 70: 401, 73: 410, 74: 411, 75: 410,
                     76: 411, 77: 410, 78: 411, 79: 410, 80: 411, 93: 414, 94: 415, 95: 416, 96: 417, 97: 418, 98: 419,
                     99: 420, 100: 421, 101: 422, 102: 423, 103: 424, 104: 425, 105: 426}
    traffic = tile.traffic
    heavy_offset = 27  # offset from the start that the heavy version of the traffic sprite is used.
    # Traffic threshold values. These should probably be moved to a data file or something as they're a mechanic and not part of this renderer.
    hwy_threshold = [30, 58]
    road_threshold = [86, 172]
    building_id = networks[tile.coordinates].building_id
    if building_id < 44:
        threshold = road_threshold
    else:
        threshold = hwy_threshold
    if traffic < threshold[0]:
        return None
    elif traffic > threshold[1] and building_id not in (93, 94, 95, 96):
        tile_id = traffic_tiles[building_id] + heavy_offset + 1000
    else:
        tile_id = traffic_tiles[building_id] + 1000
    tile_image = sprites[tile_id]
    if tile_id in (411, 438):
        tile_image = tile_image.transpose(Image.FLIP_LEFT_RIGHT)
    return tile_image

def create_things_layer(city, sprites):
    """
    Generates the thing overlay layer. This includes trains, planes, helicopters, boats (sail and cargo), nessie, emergency deploys, the monster and tornadoes.
    Note that emergency deploys do not show up in the game when loading, but are stored in the game file and this rendered here.
    Args:
        city (City): city object to draw a terrain layer from.
        sprites (dict): id: Image dictionary of sprites to use.
    Returns:
        Dictionary of (row, col): {"pixel": (x, y), "image": Image} objects for compositing.
    """
    thing_sprites = {}
    for t in city.things.items():
        thing_idx, thing_data = t
        thing_id = thing_data.thing_id
        thing_location = (thing_data.x, thing_data.y)

        if thing_data.x > 127 or thing_data.y > 127:
            continue

        # txt = city.tilelist[thing_location].text_pointer
        # print(f"{thing_idx}: {str(thing_data)}, txt: {txt}.")
        tile_w_offset = 0
        tile_h_offset = 0

        if thing_id == 0:  # Appears to be null, so don't draw anything
            continue
        elif thing_id == 1:  # Airplane
            # todo: add plane rotations
            thing_image = sprites[1359]
            tile_w_offset = -32  # Plane should be one tile to the left.
            plane_alt = 6  # Todo: airplane has variable altitude, add that.
            tile_h_offset = plane_alt * layer_offset
        elif thing_id == 2:  # Helicopter
            thing_image = sprites[1364]
            copter_alt = 4  # Todo: helicopter has variable altitude, add that.
            tile_h_offset = copter_alt * layer_offset
        elif thing_id == 3:  # Ship
            thing_image = sprites[1372]
        elif thing_id == 4:  # Unknown
            thing_image = sprites[1300]
        elif thing_id == 5:  # Monster.
            thing_image = draw_monster(sprites)
            # Monster needs special handling because it's so big. This also isn't quite pixel perfect.
            # Todo: monsters have a shadow, but only on the base terrain layer, so water or land, not on buildings.
            tile_w_offset = -128
            tile_h_offset = -int(5.5 * layer_offset)
        elif thing_id == 6:  # Unknown
            thing_image = sprites[1300]
        elif thing_id == 7:  # police deploy
            thing_image = sprites[1382]
        elif thing_id == 8:  # fire deploy
            thing_image = sprites[1383]
        elif thing_id == 9:
            if thing_data.rotation_1 == 0:
                thing_image = sprites[1380]
            # Nessie!
            if thing_data.rotation_2 == 1:
                thing_image = sprites[1379]
            else:
                thing_image = sprites[1381]
        elif thing_id in (10, 11):
            if thing_data.rotation_1 == 0:
                thing_image = sprites[1374]
            else:  # todo: handle diagonal rotations.
                thing_image = sprites[1378]
        elif thing_id == 14:  # military deploy
            thing_image = sprites[1384]
        elif thing_id == 15:  # tornado
            thing_image = sprites[1499]
            tile_w_offset = -32  # Move one tile to the left.
        else:
            thing_image = sprites[1303]
        thing_sprites[thing_location] = thing_image
        altitude = city.tilelist[thing_location].altitude
        water_table_level = city.simulator_settings["GlobalSeaLevel"]
        if altitude < water_table_level:
            altitude = water_table_level
        row, col = thing_location
        extra = thing_image.size[1] - 17
        shift = altitude * layer_offset
        i = (row * 16 - col * 16) + w_offset + tile_w_offset
        j = (row * 8 + col * 8) + h_offset + shift - extra + tile_h_offset

        thing_sprites[(row, col)] = {"pixel": (i, j), "image": thing_image}
    return thing_sprites


def draw_monster(sprites):
    """
    Draws the monster. Future feature would be to draw a random monster.
    Draw order is the two rear legs, then body, then front legs.
    Each of the two legs has two positions it can be in, and each leg can be independent from the others.

    This is some ugly special case rendering. I didn't spot what the trick was, so...
    This is also not pixel perfect with the game.
    Returns:
        An image containing the monster.
    """
    rear_upper = [1478, 1479]
    rear_lower = [1480, 1481]
    rear_claw = [1482, 1483]
    front_upper = [1484, 1485]
    front_lower = [1486, 1487]
    front_claw = [1488, 1489]
    head = [1490, 1491]

    image = Image.new('RGBA', (300, 300), (255, 255, 255, 0))

    # left rear leg
    left_rear_image = Image.new('RGBA', (87, 145), (255, 255, 255, 0))
    img = sprites[rear_claw[0]]
    left_rear_image.paste(img, (3, 95), img)
    img = sprites[rear_lower[0]]
    left_rear_image.paste(img, (26, 53), img)
    img = sprites[rear_upper[1]]
    left_rear_image.paste(img, (26, 0), img)

    # right rear leg
    right_rear_image = Image.new('RGBA', (87, 145), (255, 255, 255, 0))
    img = sprites[rear_claw[1]]
    right_rear_image.paste(img, (25, 38), img)
    img = sprites[rear_lower[1]]
    right_rear_image.paste(img, (10, 6), img)
    img = sprites[rear_upper[0]]
    right_rear_image.paste(img, (26, 0), img)
    right_rear_image = right_rear_image.transpose(Image.FLIP_LEFT_RIGHT)

    # left front leg
    left_front_image = Image.new('RGBA', (87, 145), (255, 255, 255, 0))
    img = sprites[front_claw[0]]
    left_front_image.paste(img, (9, 82), img)
    img = sprites[front_lower[0]]
    left_front_image.paste(img, (29, 32), img)
    img = sprites[front_upper[1]]
    left_front_image.paste(img, (23, 0), img)

    # right frontrear leg
    right_front_image = Image.new('RGBA', (87, 145), (255, 255, 255, 0))
    img = sprites[front_claw[1]]
    right_front_image.paste(img, (28, 51), img)
    img = sprites[front_lower[1]]
    right_front_image.paste(img, (9, 6), img)
    img = sprites[front_upper[0]]
    right_front_image.paste(img, (23, 0), img)
    right_front_image = right_front_image.transpose(Image.FLIP_LEFT_RIGHT)

    # head
    head_left = sprites[head[1]]
    head_right = sprites[head[1]]
    head_right = head_right.transpose(Image.FLIP_LEFT_RIGHT)

    image.paste(left_rear_image, (43, 38), left_rear_image)
    image.paste(right_rear_image, (169, 38), right_rear_image)

    image.paste(head_left, (86, 0), head_left)
    image.paste(head_right, (148, 0), head_right)

    image.paste(left_front_image, (43, 61), left_front_image)
    image.paste(right_front_image, (168, 61), right_front_image)

    return image


def create_disaster_layer(city, sprites):
    """
    Draws the disaster overlay, this ix the toxic cloud, flood, rioters and fires.
    Does not include monster or tornado, as those are part of XTHG and are entities, not properties of tiles.
    Args:
        city (City): city object to draw a terrain layer from.
        sprites (dict): id: Image dictionary of sprites to use.
    Returns:
        Dictionary of (row, col): {"pixel": (x, y), "image": Image} objects for compositing.
    """
    random.seed(42)  # Fire (and possibly other disaster tiles) should be deterministically randomly chosen.
    disaster_sprites = {}
    sprite_map = {0xFB: 1496, 0xFC: 1492, 0xFD: 1493, 0xFE: 1494}
    fire_ids = [1396, 1397, 1398, 1399]
    for tile_location, tile in city.tilelist.items():
        txt = tile.text_pointer
        if txt == 0xFF:
            disaster_image = sprites[fire_ids[random.randint(0, 3)]]
        elif txt in sprite_map.keys():
            disaster_image = sprites[sprite_map[txt]]
        else:
            continue
        disaster_sprites[tile_location] = disaster_image
        altitude = tile.altitude
        water_table_level = city.simulator_settings["GlobalSeaLevel"]
        if altitude < water_table_level:
            altitude = water_table_level
        row, col = tile_location
        extra = disaster_image.size[1] - 17
        shift = altitude * layer_offset
        i = (row * 16 - col * 16) + w_offset
        j = (row * 8 + col * 8) + h_offset + shift - extra

        disaster_sprites[(row, col)] = {"pixel": (i, j), "image": disaster_image}
    return disaster_sprites


def draw_edge(city, sprites, position):
    """
    draws the edge stack image, made of water and land edge tiles.
    Args:
        city (City): city object to draw a terrain layer from.
        sprites (dict): id: Image dictionary of sprites to use.
        position (tuple): (x, y) coordinate pair for where to generate the edge stack from.
    Returns:
        Returns an image containing the stack.
    """
    water_edge_id = 1284
    land_edge_id = 1269
    tile = city.tilelist[position]
    altitude = tile.altitude
    row, col = position
    water_table_level = city.simulator_settings["GlobalSeaLevel"]
    stack_height = abs(layer_offset * altitude)
    if altitude < water_table_level:
        stack_height += abs(layer_offset * (water_table_level - altitude))
    image = Image.new('RGBA', (32, stack_height + 17), (0, 0, 0, 0))
    for a in range(altitude):
        j = stack_height + (a + 1) * layer_offset
        land_edge = sprites[land_edge_id]
        image.paste(land_edge, (0, j), land_edge)
    for a in range(altitude, water_table_level):
        j = stack_height + (a + 1) * layer_offset
        water_edge = sprites[water_edge_id]
        image.paste(water_edge, (0, j), water_edge)
    a = (row * 16 - col * 16) + w_offset
    b = (row * 8 + col * 8) + h_offset - stack_height
    return {position: {"pixel": (a, b), "image": image}}


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
