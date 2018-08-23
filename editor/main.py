import sys
from collections import namedtuple
import argparse
from datetime import datetime

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import Filename, Texture, OrthographicLens, PNMImage, Point2, NodePath, TextureStage, WindowProperties
from panda3d.core import TextNode, TransparencyAttrib, Lens, loadPrcFile, ConfigVariableString, CardMaker, \
    AntialiasAttrib, Filename

import city_draw as cd


sys.path.append('..')

loadPrcFile("config.prc")

Point = namedtuple("Point", ['x', 'y'])
TILE_WIDTH = 32  # Width of a tile in pixels.
TILE_HEIGHT = 16  # Height of a tile in pixels.



def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--city', dest="input_file", help="path to city to open", metavar="FILE", required=True)
    parser.add_argument('-s', '--sprites', dest="sprites_dir", help="path to the directory containing the sprites", metavar="FILE", required=True)

    args = parser.parse_args()
    return args


def color_convert(r, g, b, a=255):
    """
    Converts from an 32b colour to a float colour.
    """
    return tuple(max(0, min(255, x)) / 255 for x in (r, g, b, a))


def convert_pixel_to_screen(x, y):
    """
    Converts pixel x/y coordinates to screen coordinates.
    """
    win_x, win_y = base.win.getSize()
    new_x = x / win_x
    new_y = y / win_y
    return new_x, new_y


def load_sprite(texture_file=None):
    fn = Filename(texture_file)
    image = PNMImage(fn)
    w = image.getXSize()
    h = image.getYSize()
    new_w, new_h = convert_pixel_to_screen(w, h)
    sprite_image = Texture()
    sprite_image.load(image)

    # Needed to keep the textures from looking blurry.
    sprite_image.setMagfilter(Texture.FTNearest)
    sprite_image.setMinfilter(Texture.FTNearest)

    cm = CardMaker(texture_file)
    cm.setFrame(0, new_w, 0, new_h)
    card = render.attachNewNode(cm.generate())
    card.setTexture(sprite_image)
    card.setTransparency(TransparencyAttrib.MAlpha)
    card.setAntialias(AntialiasAttrib.MNone)
    return card, w

def load_city(city_path):
    city = cd.City()
    city.create_city_from_file(city_path)
    return city

class OpenCity2k(ShowBase):
    class Sprite:
        def __init__(self, sprite_path):
            self.sprite, w = load_sprite(sprite_path)
            self.width = w

        def getPos(self, *args):
            return self.sprite.getPos(*args)

        def setPos(self, *args):
            self.sprite.setPos(*args)

        def instanceTo(self, n):
            self.sprite.instanceTo(n)


    def __init__(self, city_path, sprites_dir):
        print(f"{datetime.now()}: Started init.")
        ShowBase.__init__(self)

        self.disableMouse()
        self.setBackgroundColor(color_convert(55, 23, 0))
        self.accept("escape", sys.exit)  # Escape quits
        self.gameTask = taskMgr.add(self.gameLoop, "gameLoop")
        self.camera_setup()
        self.is_down = base.mouseWatcherNode.is_button_down
        # self.resize = base.
        self.sprites = {}
        print(f"{datetime.now()}: Finished engine init..")
        self.city = load_city(city_path)
        print(f"{datetime.now()}: City loaded.")
        self.load_sprites(sprites_dir)
        print(f"{datetime.now()}: Sprites loaded.")
        self.draw_terrain()
        print(f"{datetime.now()}: Terrain drawn.")

        # self.terrain_root = render.attachNewNode("terrain root")
        # self.buildings_root = render.attachNewNode("buildings root")

    def load_sprites(self, sprites_dir):
        for sprite_id in range(1001, 1500):
            sprite = self.Sprite(f"{sprites_dir}{sprite_id}.png")
            self.sprites[sprite_id] = sprite

    def draw_terrain(self):
        # sea_level = self.city.city_attributes["GlobalSeaLevel"]
        sea_level = 6
        for row in range(127, -1, -1):
            for col in range(127, -1, -1):
                tile = self.city.tilelist[(row, col)]
                terrain_id = 1000 + cd.terrain_to_id(tile)
                if row == 13 and col == 9:
                    print(tile)

                alt = tile.altitude
                if alt < sea_level:
                    alt = sea_level
                s = self.sprites[terrain_id]
                x = render.attachNewNode(f"{row}, {col}: {terrain_id}")
                cd.set_idx_pos(x, s.width, row, col, alt)
                s.instanceTo(x)

    def camera_setup(self):
        lens = OrthographicLens()
        self.cam.node().setLens(lens)
        self.cam.setPos(0, 0, 0)

    def mover(self, to_move):
        curr = to_move.getPos()
        inc = 0.01
        if self.is_down('e'):
            to_move.setPos((curr[0], curr[1] - inc, curr[2]))
        elif self.is_down('q'):
            to_move.setPos((curr[0], curr[1] + inc, curr[2]))
        elif self.is_down('a'):
            to_move.setPos((curr[0] - inc, curr[1], curr[2]))
        elif self.is_down('d'):
            to_move.setPos((curr[0] + inc, curr[1], curr[2]))
        elif self.is_down('s'):
            to_move.setPos((curr[0], curr[1], curr[2] - inc))
        elif self.is_down('w'):
            to_move.setPos((curr[0], curr[1], curr[2] + inc))
        elif self.is_down('z'):
            to_move.setPos((0, 0, 0))

    def resize(self, args):
        # print(f"Window resized to: {args}.")
        self.draw_terrain()

    def gameLoop(self, task):
        self.mover(self.camera)
        # self.accept('window-event', self.resize)
        return Task.cont


if __name__ == "__main__":
    options = parse_command_line()
    filename = options.input_file
    sprites_dir = options.sprites_dir
    app = OpenCity2k(filename, sprites_dir)
    app.run()
