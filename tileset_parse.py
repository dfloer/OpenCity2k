import sc2_iff_parse as sc2ip
import image_parse
from utils import open_file, trim_cstring

"""
Library to parse the .mif files for tilesets, as per spec here:
https://github.com/dfloer/SC2k-docs/blob/master/sprite%20data%20spec.md#mif-files
"""


def open_and_uncompress_mif_file(input_filename):
    """
    Opens an input file and returns the uncompressed contents, ready for further parsing.
    Args:
        input_filename (path): path the the .mif file to open.
    Returns:
        Uncompressed MIFF data.
    """
    raw_sc2_file = open_file(input_filename)
    compressed_data = sc2ip.chunk_input_serial(raw_sc2_file, 'mif')
    uncompressed_data = sc2ip.sc2_uncompress_input(compressed_data, 'mif')
    return uncompressed_data


def trim_name(name):
    """
    Trims bytes off of the end of a cstring and returns the nice name.
    Args:
        name (bytes): raw bytes representing the name.
    Returns:
        The cleaned name
    """
    return trim_cstring(name)


class Shape:
    def __init__(self, raw_data=None, raw_name=None):
        self.name = ""
        self.building = None
        self.pixels = []

        if raw_name != None:
            self.name = trim_name(raw_name[4:])
            # Number from 0..255 that corresponds the that building in XBLD, only set with a custom name.
            self.building = int.from_bytes(raw_name[1: 2], byteorder='big')
        self.id = int.from_bytes(raw_data[0: 2], byteorder='big')
        self.width = int.from_bytes(raw_data[2: 4], byteorder='big')
        self.height = int.from_bytes(raw_data[4: 6], byteorder='big')
        self.data_length = int.from_bytes(raw_data[6: 10], byteorder='big')
        self.pixel_data = raw_data[10:]
        self.pixel_rows = image_parse.split_data(self.pixel_data)
        try:
            self.img_array = self.rows_to_array()
        except Exception as ex:
            print(f"header:", "id {self.id}, w {self.width}, h {self.height}, len {self.data_length}")
            print(ex)
            raise

    def rows_to_array(self):
        """
        Generates a pixel array from a 1D list of pixels.
        Returns:
            Pillow image array.
        """
        width = self.width
        height = self.height
        pixel_rows = self.pixel_rows
        return image_parse.create_image(pixel_rows, height, width)

    def create_sprite(self, outfile, palette_colours, mode='png', animate=False):
        """
        Creates the actual sprite.
        Args:
            outfile (str): Path to the output file.
            palette_colours (pillow image array): Palette to generate the image with.
            mode (str): bmp or png.
            animate (bool): create animated sprites.
        Returns:
            True if the file was created, else False.
        """
        # Check to see if the output array has anything in it, or if we just had a blank tile.
        # Note: This implementation fails if a tileset legit had a 1px high tile in it.
        if self.height != 1:
            output_file = "{}{}".format(outfile, str(self.id))
            image_parse.draw_image(self.img_array, self.height, self.width, palette_colours, output_file, mode, animate)
            return True
        else:
            return False

    def __len__(self):
        return len(self.pixel_data)


def parse_miff(miff_data):
    """
    Iterates through the data making sprites for each tile.
    Args:
        miff_data (bytes): raw bytes to parse.
    Returns:

    """
    shapes_array = []
    shap_data = miff_data["TILE"][2 : ]
    chunk_tiles = sc2ip.mif_parse_tile(shap_data)

    name_data = None
    for x in chunk_tiles:
        tile_type = x[0]
        data = x[1]
        if tile_type == 'NAME':
            name_data = data
        else:
            new_shape = Shape(raw_data=x[1], raw_name=name_data)
            shapes_array.append(new_shape)
    return shapes_array
