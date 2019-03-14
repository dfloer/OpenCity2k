import sys


import main

sys.path.append('..')
import sc2_parse as sc2p

TILE_WIDTH = main.TILE_WIDTH
TILE_HEIGHT = main.TILE_HEIGHT
ALTITUDE_OFFSET = 4


def convert_iso_to_screen(row_idx, col_idx, width, altitude, layer=0):
    """
    Converts a row and column index into screen coordinates.
       /\       Tile 1 has coordinates (0, 0).
      /1 \      Tile 2 has coordinates (0, 1).
     /\  /\     Tile 3 has coordinates (1, 1).
    /2 \/4 \    Tile 4 has coordinates (1, 0).
    \  /\  /
     \/3 \/
      \  /
       \/
    Width is important for non 1x1 tiles.
    """
    height_offset = (width // TILE_WIDTH) * TILE_HEIGHT // 2
    altitude_offset = altitude * ALTITUDE_OFFSET
    screen_x = -(col_idx - row_idx) * TILE_WIDTH // 2
    screen_y = -((row_idx + col_idx) * TILE_HEIGHT // 2) - height_offset - altitude_offset
    # This'll need to handle z as well.
    a, b = main.convert_pixel_to_screen(screen_x, screen_y)
    screen_z = 100 + layer  # todo: handle this properly.
    return a, screen_z, b


def convert_screen_to_iso(screen_x, screen_y):
    """
    Converts screen coordinates to the isometric tile coordinates.
    This does not take altitude into account.
    Args:
        screen_x (float): screen coordinate x
        screen_y (float): screen coordinate y
    Returns:
        (x, y) tuple containing the isometric tile coordinates.
    """
    w = 800
    h = 600
    iso_x = ((screen_y * 2 / TILE_HEIGHT) + (screen_x / TILE_WIDTH)) / 2
    iso_y = (screen_y * 2 / TILE_HEIGHT) - iso_x
    return iso_x, iso_y



def set_idx_pos(sprite, sprite_width, row, col, alt, lay):
    row -= alt
    col -= alt
    p = convert_iso_to_screen(row, col, sprite_width, alt, lay)
    sprite.setPos(p)


class City(sc2p.City):
    """
    Extensions to the city class for panda3d drawing related functions.
    Leave the base class general enough for loading and parsing a city.
    """
    def __init__(self, *args, **kwargs):
        super(City, self).__init__(*args, **kwargs)


class Tile(sc2p.Tile):
    """
    Extensions to the Tile class for panda3d drawing related functions.
    Leave the base class general, and extend it as needed.
    """
    def __init__(self, *args, **kwargs):
        super(Tile, self).__init__(*args, **kwargs)
        self.test = 42

    def draw_tile_terrain(self, parent_node):
        """
        Handles drawing of a terrain tile. Does this by adding it to the panda3d scene graph
        Args:
            parent_node (panda3d node): Node to parent
        """
        pass

def terrain_to_id(self):
    """
    Converts an XTER id to the sprite file we need to load.
    Args:
        terrain (int): xter value
        water (bool): is this tile covered in water?
    Returns:
        An integer corresponding to the sprite id to use.
    """
    ground = range(0, 0xf)
    underwater = range(0x10, 0x1f)
    shoreline = range(0x20, 0x2f)
    surface_water = range(0x30, 0x3f)
    more_surface_water = range(0x40, 0x46)
    tile_id = 256
    terrain = self.terrain
    if terrain in ground:
        tile_id = 256 + terrain
    elif terrain in shoreline:
        tile_id = 256 + terrain - 18
    elif terrain in surface_water:
        tile_id = 256 + terrain - 34
    elif terrain in more_surface_water:
        tile_id = 256 + terrain - 35
    elif self.is_water or terrain in underwater:
        tile_id = 270
    return tile_id
