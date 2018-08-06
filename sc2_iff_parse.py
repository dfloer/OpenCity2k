#!/usr/bin/env python

import collections
import itertools
from utils import open_file, write_file_contents, get_padded_bytes, parse_int32, parse_uint32

SC2_SIZE_DICT = collections.OrderedDict((('CNAM', 32), ('MISC', 4800), ('ALTM', 32768), ('XTER', 16384), ('XBLD', 16384),
        ('XZON', 16384), ('XUND', 16384), ('XTXT', 16384), ('XLAB', 6400), ('XMIC', 1200),
        ('XTHG', 480), ('XBIT', 16384), ('XTRF', 4096), ('XPLT', 4096), ('XVAL', 4096), ('XCRM', 4096),
        ('XPLC', 1024), ('XFIR', 1024), ('XPOP', 1024), ('XROG', 1024), ('XGRP', 3328), ('TEXT', 0), ('SCEN', 0), ('PICT', 0),))
SCENARIO_CHUNKS = ('TEXT', 'SCEN', 'PICT')

SC2 = True


# Exception classes so that raised exceptions can be more descriptive.
class IFFParse(Exception):
    """
    Base class for exceptions.
    """
    pass


class SC2Parse(IFFParse):
    """
    Exceptions for when parsing a SC2 file fails.
    """
    def __init__(self, message):
        self.message = message


class MIFFParse(IFFParse):
    """
    Exceptions for when parsing a MIFF file fails.
    """
    def __init__(self, message):
        self.message = message


# Functions dealing with opening and parsing the basic contents of the IFF files.
def check_file(input_data, input_type):
    """
    Does some basic checks of the file to make sure it's valid and includes special handling for the Mac version of the game. The IFF standard is from 1985, so it's not super robust...
    Untested with some of the weirder versions of SC2k, such as Amiga, PocketPC/Windows Mobile, etc.
    Currently only supports parsing for FORM and MIFF files.
    Args:
        input_data (bytes): bytes containing the entirety of the city.
        input_type (str): type of input file, supported are 'mif' for .mif tileset/MIFF file and 'sc2' for .sc2 city file.
    Returns:
        A tuple containing a dictionary and the input.
        The dictionary looks like {'type_id': header, 'data_size': reported_size, 'file_type': file_type} where the header is the opening 4 bytes of input as a bytestring, reported_size is an int of the size the file claims to be and file_type is one of b"SC2K" (tileset) of b"SCDH" (city).
    Raises:
        SC2Parse: an error relating to parsing .sc2 files. Could be caused by the file being a SimCity classic city (currently an unsupported format), not a city file at all, or being corrupted.
        MIFFParse: an error relating to parsing .mif files. Could be caused by file corruption of not actually being a tileset file.
    """
    # Check and convert if this is a Mac city file.
    if mac_check(input_data):
        input_data = mac_fix(input_data)
    # This should be "FORM" for .sc2
    header = input_data[0 : 4]
    # The reported size saved in the .sc2, we don't count the first 8 bytes though, so we need to add them back.
    reported_size = parse_int32(input_data[4 : 8]) + 8
    # This should be "SCDH"
    file_type = input_data[8 : 12]
    # Actual size of our input file
    actual_size = len(input_data)
    # Check and see if this is a Simcity Classic city.
    if input_type == 'sc2':
        if header != b"FORM":
            # Check and see if this is a Simcity Classic city.
            if input_data[0x41 : 0x49] == b'\x43\x49\x54\x59\x4D\x43\x52\x50' and header[0 : 2] == b'\x00\x0d':
                error_message = "Simcity Classic city files are not supported."
            else:
                error_message = f"Not a FORM type IFF file, claiming: {header}"
            raise SC2Parse(error_message)
        if reported_size != actual_size:
            error_message = "File reports being: {reported_size}B, but is actually {actual_size}B long."
            raise SC2Parse(error_message)
        if file_type != b"SCDH":
            error_message = f"File type is not SCDH, claiming: {file_type}"
            raise SC2Parse(error_message)
    elif input_type == 'mif':
        if header != b"MIFF":
            error_message = f"Not a MIFF type IFF file, claiming: {header}"
            raise MIFFParse(error_message)
        if reported_size != actual_size:
            error_message = f"File reports being: {reported_size}B, but is actually {actual_size}B long."
            raise MIFFParse(error_message)
        if file_type != b"SC2K":
            error_message = "File type is not SC2K, claiming: {file_type}"
            raise MIFFParse(error_message)
    return {'type_id': header, 'data_size': reported_size, 'file_type': file_type}, input_data


def mac_check(input_data):
    """
    Checks if this is a Mac .sc2 file.
    Args:
        input_data (bytes): raw city information.
    Returns:
        True if this is a Mac formatted file, False if it isn't.
    """
    header = input_data[0 : 4]
    mac_form = input_data[0x80 : 0x84]
    if header != b"FORM" and mac_form == b"FORM":
        return True
    else:
        return False


def mac_fix(input_data):
    """
    Makes a Mac city file compatible with the Win95 version of the game.
    Basically, we don't need the first 0x80 bytes from the Mac file, something about a resource fork. Also, some of the files have garbage data at the end, which is also trimmed.
    Args:
        input_data (bytes): raw city information.
    Returns:
        Bytes comprising a compatible SC2k Win95 city file from the Mac file.
    """
    reported_size = parse_int32(input_data[0x84 : 0x88]) + 8
    return input[0x80 : 0x80 + reported_size]


# Functions to handle chunking up the IFF file.
def get_chunk_from_offset(input_data, offset):
    """
    Parses an IFF chunk by reading the header and using the size to determine which bytes belong to it.
    An IFF chunk has an 8 byte header, of which the first 4 bytes is the type and the second 4 bytes is the size (exclusive of the header).
    Args:
        input_data (bytes): raw city information.
        offset (int): starting offset in input to start parsing at.
    Returns:
        A list containing the id of the chunk (a 4 byte ascii value), an int length of the chunk of finally bytes of the chunk data.
    """
    location_index = offset
    chunk_id = input_data[location_index : location_index + 4].decode('ascii')
    # Maximum 32b/4B, so 2^32 in length.
    chunk_size = parse_uint32(input_data[location_index + 4 : location_index + 8])
    chunk_data = input_data[location_index + 8 : location_index + 8 + chunk_size]
    return [chunk_id, chunk_size, chunk_data]


def get_chunk_from_name(input_data, section_name):
    """
    Gets the specified chunk based on its name and parses it.
    Warning!: This could be fragile if there's a sign with "XZON" in it, or similar.
    Args:
        input (bytes): raw city information.
        section_name (str): ASCII convertible name of the IFF section/chunk id to get.
    Returns:
        A list containing the id of the chunk (a 4 byte ascii value), an int length of the chunk of finally bytes of the chunk data.
    """
    return get_chunk_from_offset(input_data, input_data.index(bytes(section_name, 'ascii')))


def get_n_bytes(iterable, n, fill=None):
    """
    Splits the input iterable up every n bytes, and pads it if it's shorter.
    For example, if iterable is a list of 31 bytes and n is 8, there will be 4 resulting iterators, with the last entry in the last one being whatever value fill has.
    Args:
        iterable (bytes): raw city information.
        n (int): number of bytes to split on.
        fill (bytes): if iterable isn't cleanly divided by n, fill any elements up with this value.
    Returns:
        An iterator splitting the input up every n bytes, padded out to always be a multiple of n bytes long.
    """
    args = [iter(iterable)] * n
    output = itertools.zip_longest(*args, fillvalue=fill)
    return output


# Functions to handle compression and decompression of the IFF file.
def uncompress_rle(encoded_data):
    """
    Uncompresses the RLE compressed city data. For more information, consult the .sc2 file format specification documents at https://github.com/dfloer/SC2k-docs
    Args:
        encoded_data (bytes): raw city information.
    Returns:
        Uncompressed bytes.
    """
    decoded_data = bytearray()
    next_byte_repeat = False
    byte_count = 0

    # Data is stored in two forms: 0x01..0x7F and 0x81..0xFF
    for byte in encoded_data:
        if byte < 0x80 and byte_count == 0:
            # In this case, byte is a count of the number of data bytes that follow.
            byte_count = byte
            next_byte_repeat = False
        elif byte > 0x80 and byte_count == 0:
            # In this case, byte-127=count of how many times the very next byte repeats.
            byte_count = byte - 0x7f
            next_byte_repeat = True
        else:
            if byte_count > 0 and next_byte_repeat:
                decoded_data.extend([byte] * byte_count)
                byte_count = 0
            elif byte_count > 0 and not next_byte_repeat:
                decoded_data.extend([byte])
                byte_count -= 1
    return decoded_data


def compress_rle(uncompressed_data):
    """
    Compresses city data with a generally comparable algorithm as SC2k uses stock. See .sc2 file spec for full details at https://github.com/dfloer/SC2k-docs
    Args:
        uncompressed_data (bytes): Uncompressed data
    Returns:
        Compressed bytes.
    """
    # Count the bytes we have, and create a tuple (to make sure ordering is preserved) of a count and then the number of bytes following.
    counted_bytes = ([(len(list(bytes_counted)), count) for count, bytes_counted in itertools.groupby(uncompressed_data)])
    compressed_data = bytearray()
    temp = bytearray()
    offset = 0
    for count, byte in counted_bytes:
        data = uncompressed_data[offset: offset + count]
        if count == 1:
            # The spec can't have more than 127 repeated bytes, so if we do, we need to start another run to encode.
            if len(temp) == 127:
                compressed_data.extend([len(temp)])
                compressed_data.extend(temp)
                temp = bytearray()
            temp.extend(data)
        else:
            chunks = [data[x : x + 0x80] for x in range(0, len(data), 0x80)]
            if len(temp) != 0:
                compressed_data.extend([len(temp)])
                compressed_data.extend(temp)
                temp = bytearray()
            for chunk in chunks:
                compressed_data.extend([len(chunk) + 0x7f, byte])
        offset += count
    if len(temp) != 0:
        compressed_data.extend([len(temp)])
        compressed_data.extend(temp)
    return compressed_data


def uncompress_rle_hex(encoded_data):
    """
    Convenience function that generates a hex representation of the data. Useful for working around print() decoded binary data.
    Args:
        encoded_data (bytes): binary data.
    Returns:
        List of strings of hexadecimal representation of input data.
    """
    return [hex(x) for x in encoded_data]


# Functions to handle decompression and compression of the actual city information.
def chunk_input_serial(input_file, input_type='sc2'):
    """
    Takes already uncompressed city data and converts it into chunks.
    Args:
        input_file (bytes): raw uncompressed city data.
        input_type (str): type of the input file we're opening.
    Returns:
        A dictionary of {chunk id: chunk data} form, one entry per chunk.
    Raises:
        SC2Parse: re-raised errors from check_file()
    """
    output_dict = collections.OrderedDict()
    try:
        header, infile = check_file(input_file, input_type)
    except SC2Parse:
        raise
    file_length = header['data_size']
    # -12B for the header
    remaining_length = file_length - 12

    while remaining_length > 0:
        offset = file_length - remaining_length
        chunk = get_chunk_from_offset(input_file, offset)
        chunk_id = chunk[0]
        chunk_data = chunk[2]
        if chunk_id == "TEXT":
            try:
                output_dict[chunk_id] += [chunk_data]
            except KeyError:
                output_dict[chunk_id] = [chunk_data]
        else:
            output_dict[chunk_id] = chunk_data
        # How much of the file still needs to be scanned? Subtract the size of the chunk's data and header from it.
        remaining_length -= (chunk[1] + 8)
    return output_dict


def sc2_uncompress_input(input_file, input_type='sc2'):
    """
    Uncompresses a compressed .mif or .sc2 file.
    For a .sc2 file, doesn't uncompress chunks with id of CNAM or ALTM and for .mif, soesn't uncompress TILE chunks.
    Args:
        input_file (bytes): compressed city data.
        input_type (str): type of the input file we're opening.
    Returns:
        A dictionary of uncompressed {chunk id: chunk data} form, one entry per chunk.
    """
    uncompressed_dict = collections.OrderedDict()
    for k, v in input_file.items():
        if input_type == 'sc2':
            if k not in ("CNAM", "ALTM", "TEXT", "SCEN"):
                uncompressed_dict[k] = uncompress_rle(v)
            elif k == "TEXT":
                uncompressed_dict[k] = [bytearray(x) for x in v]
            else:
                uncompressed_dict[k] = bytearray(v)
        elif input_type == 'mif':
            if k != "TILE":
                uncompressed_dict[k] = uncompress_rle(v)
            else:
                uncompressed_dict[k] = bytearray(v)
    return uncompressed_dict


def mif_parse_tile(tile_data):
    """
    Splits a .mif file into a list of tiles for further parsing.
    Args:
        tile_data (bytes): compressed city data:
    Returns:
       A list of tiles.
    """
    output = []
    file_length = len(tile_data)
    remaining_length = file_length
    while remaining_length > 0:
        offset = file_length - remaining_length
        chunk = get_chunk_from_offset(tile_data, offset)
        output.append([chunk[0], chunk[2]])
        #How much of the file still needs to be scanned? Subtract the size of the chunk's data and header from it.
        remaining_length -= ((chunk[1]) + 8)
    return output


def clean_city_name(dirty_name):
    """
    Get's the city's name, if it exists. Sometimes CNAM contains garbage, so this also cleans that up.
    Args:
        dirty_name (bytes): City's name, possible with garbage in it.
    Returns:
        A string of the name, with garbage removed.
    """
    clean_name = ""
    dirty_name = dirty_name[1 : 32]
    for x in dirty_name:
        if x == 0x00:
            break
        clean_name += chr(x)
    return str(clean_name)
