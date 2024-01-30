from PIL import Image, ImageFont, ImageDraw
import argparse
import sys
from os import path
import random

sys.path.append('..')
import sc2_parse as sc2p
from Data.buildings import get_size as get_building_size
from Data.buildings import train_tiles


# Some important tile rendering constants.
image_width = 32 * 128 + 1000
image_height = 16 * 128 + 1000
w_offset = image_width // 2
h_offset = 500
layer_offset = -12


def draw_terrain_layer(city, sprites, groundcover=True, networks=True, zones=True, building_type="full", signs=True):
    """
    Creates an array of the tiles for terrain layer, optionally with groundcover (trees).

    Notes on how highway drawing is handled, as a special case.
    First, why? Highway tiles are the only 2x2 buildings that show the tiles underneath them. All the rest cover the underlying terrain up.
    In create_network_layer(), when we have a 2x2 highway tile, we create an extra entry for the bottom tile, which will otherwise get over-written.
    We then composite this tile *again* over-top of the terrain tile, after cropping it to just the area that shows up over the terrain tile.
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
        network_layer, highway_extra = create_network_layer(city, sprites)
    building_layer = {}
    if building_type != "none":
        building_layer = create_buildings(city, sprites)
    sign_layer = {}
    if signs:
        sign_layer = create_sign_layer(city)
    things_layer = create_things_layer(city, sprites)
    disaster_layer = create_disaster_layer(city, sprites)
    terrain_layer_image = Image.new('RGBA', (image_width, image_height), (0, 0, 0, 0))
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
            highway_lower = None
            if k in highway_extra.keys():
                source_key = highway_extra[k]
                y2 = terrain_image.size[1]
                highway_img = network_layer[source_key]["image"]
                iy = highway_img.size[1]
                c = (16, iy - y2, 48, iy)
                highway_lower = highway_img.crop(c)
            if highway_lower is not None:
                terrain_image = terrain_image.copy()
                terrain_image.paste(highway_lower, (0, 0), highway_lower)
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
        if k in sign_layer.keys():
            sign = sign_layer[k]
            sign_image = sign["image"]
            sign_position = sign["pixel"]
            terrain_layer_image.paste(sign_image, sign_position, sign_image)
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
        Dictionary of (row, col): (corner_row, corner_col) for extra highway tiles that need to be re-composited.
    """
    traffic_tiles = {29: 400, 30: 401, 31: 402, 32: 403, 33: 404, 34: 405, 35: 406, 36: 407, 37: 408, 38: 409, 39: 401,
                     40: 400, 41: 401, 42: 400, 43: 401, 67: 400, 68: 401, 69: 400, 70: 401, 73: 410, 74: 411, 75: 410,
                     76: 411, 77: 410, 78: 411, 79: 410, 80: 411, 93: 414, 94: 415, 95: 416, 96: 417, 97: 418, 98: 419,
                     99: 420, 100: 421, 101: 422, 102: 423, 103: 424, 104: 425, 105: 426}
    network_sprites = {}
    highway_extra = {}
    for k in city.networks.keys():
        row, col = k
        highway_special = False
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
            image = composite_traffic(tile, city, sprites, image)
        if rotate:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        # Highways are weird and need to be handled specially, or they "float".
        # Todo: this still has a bug in it, because highways should be drawn in the buildings layer, probably.
        # back side rampsRamps
        if building_id in (98, 99):
            shift += 20
            highway_special = True
        # Corners, Interchange, Reinforced Bridge, front ramps
        elif building_id in (97, 100, 101, 102, 103, 104, 105, 106, 107):
            # This is a workaround for a bug in the game. There's an off-by-one error somewhere in the game code, which means that this highway tile is misplaced in the save.
            if k[0] == 126 and tile.terrain == 0b1101:
                shift += 20
            else:
                shift += 8
            highway_special = True
        r, c = building.tile_coords
        i = (r * 16 - c * 16) + w_offset
        j = (r * 8 + c * 8) + h_offset + shift - extra
        network_sprites[(r, c)] = {"pixel": (i, j), "image": image}
        if highway_special:
            highway_extra[(r + 1, c)] = (r, c)
    return network_sprites, highway_extra


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
    hwy_threshold = [28, 56]
    road_threshold = [85, 170]
    building_id = networks[tile.coordinates].building_id
    # 88/89 are the causeway bridge and raised version pieces.
    if building_id < 73 or building_id in (88, 89):
        threshold = road_threshold
    else:
        threshold = hwy_threshold
    if traffic < threshold[0]:
        return None
    elif traffic > threshold[1] and building_id not in (93, 94, 95, 96):
        if building_id > 96:
            heavy_offset -= 4
        tile_id = traffic_tiles[building_id] + heavy_offset + 1000
    else:
        tile_id = traffic_tiles[building_id] + 1000
    # The straight highway tiles need to be handled differently, because there are two directions of travel for these.
    coords = tile.coordinates
    if building_id in (73, 74, 75, 76, 77, 78, 79, 80):
        # Even tile IDs are top-left bottom-right, odd are top-right bottom-left.
        if building_id % 2 == 1:
            if coords[0] % 2 == 0:
                tile_id == 410 if traffic < threshold[1] else 437
            else:
                tile_id == 411 if traffic < threshold[1] else 438
        else:
            if coords[1] % 2 == 0:
                tile_id == 410 if traffic < threshold[1] else 437
            else:
                tile_id == 411 if traffic < threshold[1] else 438
    tile_image = sprites[tile_id]
    if building_id in (74, 76, 78, 80):
        tile_image = tile_image.transpose(Image.FLIP_LEFT_RIGHT)
    return tile_image

def composite_traffic(tile, city, sprites, tile_image):
    """
    Handles compositing of the traffic tile onto the road exactly as the game does it.
    This keeps traffic from drawing over power lines, but also means that it draws under crosswalks.
    Args:
        tile (Tile): Tile data to work with.
        city (City): city object to draw a terrain layer from.
        sprites (dict): id: Image dictionary of sprites to use.
        tile_image (Image): Road tile image to composite on top of.

    Returns:
        Image: Composited traffic tile image.
    """
    traffic_image = get_traffic_image(tile, city.networks, sprites)
    if traffic_image:
        traffic_image_offset = tile_image.size[1] - traffic_image.size[1]
        # This extra mask generation step is so that traffic doesn't draw on top of power lines, railroad tracks and crosswalks.
        # There's probably a better way of doing this, but it works for now.
        mask = Image.new('RGBA', (traffic_image.size), (0, 0, 0, 0))
        w, h = traffic_image.size
        for x in range(w):
            for y in range(h):
                p = traffic_image.getpixel((x, y))
                base_p = tile_image.getpixel((x, y + traffic_image_offset))
                # We only want to draw if we're a car (blue or black), but only on something road coloured.
                # Yes, this means that the cars draw *under* the crosswalk and traintracks, but it's this was in the original game.
                # Possible tweak here is to only not draw when base_p is not (0, 0, 0, 255) (black).
                if p != (140, 140, 140, 255) and base_p == (143, 143, 143, 255):
                    mask.putpixel((x, y), p)
        # It doesn't look like anything but the straight highway pieces use the masking method.
        # This can be seen on the ramps to the bridge, where the "railing" is over-ridden by the traffic in game.
        if city.networks[tile.coordinates].building_id not in (97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107):
            tile_image.paste(traffic_image, (0, traffic_image_offset), mask)
        else:
            tile_image.paste(traffic_image, (0, traffic_image_offset), traffic_image)
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
        elif thing_id == 4:  # Unknown, but it doesn't appear to actually draw in game.
            continue
            # thing_image = sprites[1300]
        elif thing_id == 5:  # Monster.
            thing_image = draw_monster(sprites)
            # Monster needs special handling because it's so big. This also isn't quite pixel perfect.
            # Todo: monsters have a shadow, but only on the base terrain layer, so water or land, not on buildings.
            tile_w_offset = -128
            tile_h_offset = -int(5.5 * layer_offset)
        elif thing_id == 6:  # explosion
            thing_image = sprites[1387]
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
        # train
        elif thing_id in (10, 11, 12, 13):
            try:
                building_id = city.tilelist[thing_location].building.building_id
            # Also check the network layer, this is probably only for highway tiles.
            except AttributeError:
                try:
                    building_id = city.networks[thing_location].building_id
                # If thing_id is 12 or 13, this usually means it's in a subway tunnel.
                # But in at least one city, it meant surface trains.
                # So if there really isn't a building here, don't render a train.
                except KeyError:
                    continue
            # Only draw train when it is on train tracks.
            if building_id not in train_tiles:
                continue
            thing_image, tile_h_offset, tile_w_offset = get_train_tile(building_id, city, sprites, thing_location)
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

def get_train_tile(building_id, city, sprites, thing_location):
    """
    Gets the train tile for a given track tile.
    Just gonna ignore the rotations here and do it based off of the underlying tile.
    Should eventually reverse engineer it, but it doesn't quite make sense yet.
    Args:
        building_id (int): id of the builiding
        city (City): city object to draw a terrain layer from.
        sprites (dict): id: Image dictionary of sprites to use.
        thing_location (tuple): (int, int) coordinates of the tile.
    Returns:
        Image, int, int: Image for the tile along with the height and width offset, in that order.
    """
    tile_h_offset = 0
    tile_w_offset = 0
    # top-right/bottom left straight pieces, T's, + (cross)
    if building_id in (44, 55, 57, 58, 70, 71, 78):
        thing_image = sprites[1374]
    # top-left/bottom-right straight pieces, T's
    elif building_id in (45, 54, 56, 69, 72, 77):
        thing_image = sprites[1374]
        thing_image = thing_image.copy().transpose(Image.FLIP_LEFT_RIGHT)
    # bridge pieces.
    elif building_id in (90, 91):
        thing_image = sprites[1374]
        # Bridge pieces only come in one direction and can be rotated.
        tile_h_offset = -13
        if city.tilelist[thing_location].bit_flags.rotate:
            thing_image = thing_image.copy().transpose(Image.FLIP_LEFT_RIGHT)
    # top-bottom right
    elif building_id == 50:
        thing_image = sprites[1376].copy()
        thing_image = thing_image.transpose(Image.FLIP_LEFT_RIGHT)
        tile_w_offset = -1
    # top-bottom left
    elif building_id == 52:
        thing_image = sprites[1376]
    # left-right lower
    elif building_id == 51:
        thing_image = sprites[1375]
        tile_h_offset = 8
    # left-right upper
    elif building_id == 53:
        thing_image = sprites[1375]
    # upper slopes
    elif building_id == 46:
        thing_image = sprites[1377]
        thing_image = thing_image.copy().transpose(Image.FLIP_LEFT_RIGHT)
    elif building_id == 47:
        thing_image = sprites[1377]
    elif building_id == 48:
        thing_image = sprites[1378]
    elif building_id == 49:
        thing_image = sprites[1378]
        thing_image = thing_image.copy().transpose(Image.FLIP_LEFT_RIGHT)
    # lower slopes
    elif building_id == 59:
        thing_image = sprites[1377]
        thing_image = thing_image.copy().transpose(Image.FLIP_LEFT_RIGHT)
        tile_h_offset = 8
    elif building_id == 60:
        thing_image = sprites[1377]
        tile_h_offset = 8
        # thing_image = thing_image.copy().transpose(Image.FLIP_LEFT_RIGHT)
    elif building_id == 61:
        tile_h_offset = 6
        thing_image = sprites[1378]
    elif building_id == 62:
        thing_image = sprites[1378]
        thing_image = thing_image.copy().transpose(Image.FLIP_LEFT_RIGHT)
        tile_h_offset = 6
    else:
        print(building_id)
    return thing_image, tile_h_offset, tile_w_offset


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


def create_sign_layer(city):
    """
    Draws the signs.
    Args:
        city (City): city object to draw the signs from.
    Returns:
        Dictionary of (row, col): {"pixel": (x, y), "image": Image} objects for compositing.
    """
    sign_images = {}
    try:
        for tile_location, tile in city.tilelist.items():
            txt = tile.text_pointer

            if txt in range(0x01, 0x33):
                full_sign = sign_draw_sign(tile.text)
                w, h = full_sign.size
                sign_center = w // 2

                row, col = tile_location
                tile_center = 13

                altitude = tile.altitude
                water_table_level = city.simulator_settings["GlobalSeaLevel"]
                if altitude < water_table_level:
                    altitude = water_table_level
                # + 8 to make the base of the sign sit in the middle of the tile, not the edge.
                shift = altitude * layer_offset - h + 8

                # i + 3 because the pole is 3 pixels wide, so we need that offset.
                i = (row * 16 - col * 16) + w_offset + tile_center - sign_center + 3
                j = (row * 8 + col * 8) + h_offset + shift
                sign_images[(row, col)] = {"pixel": (i, j), "image": full_sign}
    except OSError as e:
        print(f"Sign generation failed with error: {e}. Missing font?")
    return sign_images


def sign_draw_sign(sign_text):
    """
    Draws a sign with the given text.
    Args:
        sign_text (str): Text to draw to the sign. Trimmed to 23 characters.

    Returns:
        Image: Pillow image of the sign.
    """
    # I _think_ the font used in the Win95 Version for signs is probably MS Sans Serif.
    # The closest free font I could find is W95FA by Alina Sava, so lets try that.
    font = ImageFont.truetype("W95FA.otf", size=16)

    # Sign colours:
    text_colour = (0, 0, 0x43)
    sign_base = (0xBB, 0xBB, 0xBB)
    sign_hi = (0xE3, 0xE3, 0xE3)
    sign_med = (0xA9, 0xA9, 0xA9)
    sign_lo = (0x57, 0x57, 0x57)
    pole_m  = (0x99, 0x99, 0x99)

    if len(sign_text) > 23:
        sign_text = sign_text[:23]
    sign_height = 26
    left = sign_draw_sign_left(sign_hi, sign_base, sign_lo)
    right = sign_draw_sign_right(sign_hi, sign_med, sign_lo)

    sign_body = Image.new("RGBA", (500, 26), (*sign_base, 255))
    for col in range(500):
        sign_body.putpixel((col, 0), sign_hi)
        sign_body.putpixel((col, 1), sign_hi)
        sign_body.putpixel((col, 22), sign_med)
        sign_body.putpixel((col, 23), sign_lo)
        sign_body.putpixel((col, 24), sign_lo)
        sign_body.putpixel((col, 25), sign_med)

    d = ImageDraw.Draw(sign_body)
    left_width = 3
    right_width = 3
    x_pos = 5 + left_width
    y_pos = 5
    end_pad = 9
    letter_space = 1

    for letter in sign_text:
        # This draws the letter a second time one pixel off.
        # This seems to better approximate the look from Win95 SC2k, at least.
        d.text((x_pos, y_pos), letter, font=font, fill=(*text_colour, 255))
        d.text((x_pos + 1, y_pos), letter, font=font, fill=(*text_colour, 255))
        # Deal with unprintable characters.
        try:
            letter_width = font.getmask(letter).getbbox()[2] + 1
        except TypeError:
            letter_width = 9
        x_pos += letter_width + letter_space + 1

    mask = Image.new("RGBA", (3, 26), (0, 0, 0, 255))
    sign_body = sign_body.crop((0, 0, x_pos + end_pad + right_width, sign_height))
    sign_body.paste(left, (0, 0), mask)
    sign_body.paste(right, (x_pos + end_pad, 0), mask)

    pole = sign_draw_pole(sign_hi, sign_lo, pole_m)

    w, h = sign_body.size
    sign_center = w // 2
    # The -1 is because the sign pole overlaps by a single pixel.
    total_height = h + 64 - 1
    full_sign = Image.new("RGBA", (w, total_height), (0, 0, 0, 0))
    mask = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    full_sign.paste(sign_body, (0, 0), mask)
    pole_xy = (sign_center - 3, h - 1)
    full_sign.paste(pole, pole_xy, pole)
    return full_sign


def sign_draw_sign_left(c1, c2, c3):
    """
    Annoying pixel twiddling to draw the left side of the sign
    Args:
        c1 (tuple[int]): color 1
        c2 (tuple[int]):  color 2
        c3 (tuple[int]):  color 3
    Returns:
       Image: Resulting PIL image.
    """
    sign_height = 26
    image = Image.new('RGBA', (3, sign_height), (255, 255, 255, 0))
    for row in range(sign_height):
        if row == 0:
            pix = [None, c1, c1]
        elif row == 1:
            pix = [c1, c1, c1]
        elif row == 24:
            pix = [c1, c2, c3]
        elif row == 25:
            pix = [None, c1, c2]
        else:
            pix = [c1, c1, c2]
        for i, p in enumerate(pix):
            if p:
                image.putpixel((i, row), p)
    return image


def sign_draw_sign_right(c1, c2, c3):
    """
    Annoying pixel twiddling to draw the right side of the sign
    Args:
        c1 (tuple[int]): color 1
        c2 (tuple[int]):  color 2
        c3 (tuple[int]):  color 3
    Returns:
       Image: Resulting PIL image.
    """
    sign_height = 26
    image = Image.new('RGBA', (3, sign_height), (255, 255, 255, 0))
    for row in range(sign_height):
        if row == 0:
            pix = [c1, None, None]
        elif row == 1:
            pix = [c1, c1, c2]
        elif row == 25:
            pix = [c2, c2, c2]
        else:
            pix = [c3, c3, c2]
        for i, p in enumerate(pix):
            if p:
                image.putpixel((i, row), p)
    return image


def sign_draw_pole(c1, c2, c3):
    """
    Annoying pixel twiddling to draw the sign pole.
    Args:
        c1 (tuple[int]): color 1
        c2 (tuple[int]):  color 2
        c3 (tuple[int]):  color 3
    Returns:
       Image: Resulting PIL image.
    """
    pole_height = 64
    pole_width = 6
    image = Image.new('RGBA', (pole_width, pole_height), (255, 255, 255, 0))
    c1 = (0xE3, 0xE3, 0xE3)
    c2 = (0x57, 0x57, 0x57)
    c3 = (0x99, 0x99, 0x99)
    for row in range(pole_height):
        if row == 0:
            for x in (1, 2):
                image.putpixel((x, row), c1)
        elif row == 1:
            for x in range(5):
                image.putpixel((x, row), c1)
            image.putpixel((5, row), c3)
        elif row == 63:
            for x in range(2, 6):
                image.putpixel((x, row), c3)
        else:
            pix = [c1] * 2 + [c2] * 2 + [c3] * 2
            for i, p in enumerate(pix):
                image.putpixel((i, row), p)
    return image


def render_city_image(input_sc2_path, output_path, sprites_path, city=False, transprent_bg=False, crop_image=False, draw_signs=False):
    """
    Creates a PNG preview of the given city file
    Args:
        input_sc2_path (str): optional path to the input file. Either this or a city object needs to be used, and a city object will override this.
        output_path (str): output path for the preview file to save out.
        sprites_path (str): path to the sprites directory to use to draw the city.
        city (City): city object to render.
        transprent_bg (bool): Whether or not to have a transparent background or not.
        crop_image (bool, optional): Whether or not to crop the resulting image. Defaults to False.
    Returns:
        Nothing, but saves a PNG file to disk.
    """
    if not city:
        city = sc2p.City()
        city.create_city_from_file(input_sc2_path)
    sprites = load_sprites(sprites_path)


    terrain_layer = draw_terrain_layer(city, sprites, True, True, True, "full", draw_signs)
    width = image_width
    height = image_height

    if crop_image:
        final_size = terrain_layer.getbbox()
        width = final_size[2] - final_size[0]
        height = final_size[3] - final_size[1]
        terrain_layer = terrain_layer.crop(final_size)

    if not transprent_bg:
        background = Image.new('RGBA', (width, height), (55, 23, 0, 255))
    else:
        background = Image.new('RGBA', (width, height), (0, 0, 0, 0))

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
    parser.add_argument('-c', '--crop', dest="crop_image", help="crop the image to the minimal size", required=False, action="store_true", default=False)
    parser.add_argument('--signs', dest="draw_signs", help="draw signs", required=False, action="store_true", default=False)
    args = parser.parse_args()
    return args


if __name__ == "__main__":

    options = parse_command_line()
    input_file = options.input_file
    output_file = options.output_file
    image_location = options.sprites_dir
    transparent_bg = options.transparent_bg
    crop_image = options.crop_image
    draw_signs = options.draw_signs
    render_city_image(input_file, output_file, image_location, None, transparent_bg, crop_image, draw_signs)
