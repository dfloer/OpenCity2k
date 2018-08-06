from struct import pack, unpack
from collections import Iterable


def flatten(l):
    """
    Flattens a list that contains single non-iterable elements as well as iterable elements.
    Args:
        l (list): list of lists (or other iterables).
    Returns:
        Single, flat list.
    """
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def open_file(input_file):
    """
    Convenience function that opens a file and returns its binary contents.
    Args:
        input_file (path): full path of a file to open.
    Returns:
        Raw binary contents of the input file.
    """
    with open(input_file, 'rb') as f:
        return f.read()


def write_file_contents(output_file, data):
    """
    Convenience function that opens a file and writes binary content to it.
    Args:
        output_file (path): full path of a file to write to.
        data (bytes): binary data to write to the file.
    """
    with open(output_file, 'wb') as f:
        f.write(data)


def get_padded_bytes(base_10_int, n):
    """
    Converts a base 10 int into bytes with padding 0s to make it the required 4B.
    For example: 167960 padded to 8 bytes becomes b'\x00\x02\x90\x18'.
    Args:
        base_10_int (int): base 10 integer to convert.
        n (int): number of bytes to output.
    Returns:
        Padded bytestring conversion of base 10 int.
    """
    return bytes.fromhex(hex(base_10_int)[2:].zfill(n))


def parse_int32(unparsed_bytes):
    """
    Parses 4 bytes into a big endian signed integer.
    Args:
        unparsed_bytes (bytes):  4 bytes representing the int.
    Returns:
        Integer representation.
    """
    return unpack('>i', unparsed_bytes)[0]


def parse_uint32(unparsed_bytes):
    """
    Parses 4 bytes into a big endian unsigned integer.
    Args:
        unparsed_bytes (bytes):  4 bytes representing the int.
    Returns:
        Integer representation.
    """
    return unpack('>I', unparsed_bytes)[0]
