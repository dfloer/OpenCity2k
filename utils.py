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
        unparsed_bytes (bytes): 4 bytes representing the int.
    Returns:
        Integer representation.
    """
    return unpack('>I', unparsed_bytes)[0]


def parse_uint16(unparsed_bytes):
    """
    Parses 2 bytes into a big endian unsigned integer.
    Args:
        unparsed_bytes (bytes): 2 bytes representing the int.
    Returns:
        Integer representation.
    """
    return unpack('>H', unparsed_bytes)[0]


def parse_uint8(unparsed_bytes):
    """
    Parses 1 byte into a big endian signed integer.
    Args:
        unparsed_bytes (bytes): 1 bytes representing the int.
    Returns:
        Integer representation.
    """
    return unpack('>B', unparsed_bytes)[0]


def int_to_bitstring(int_input, pad=0):
    """
    Converts an into into its binary representation as a string of 0s and 1s.
    Optionally takes an argument for the length to pad to.
    Args:
        int_input (int): integer to convert.
        pad (int): Pad with 0s to this length.
    Returns:
        String representation of the input integer in binary.
    """
    return "{0:b}".format(int_input).zfill(pad)


def int_to_bytes(input_int, num_bytes, signed=False):
    """
    Converts an into the the given number of bytes. Will pad with 0x00 as needed.
    Args:
        input_int (int): integer to convert.
        num_bytes (int): number of bytes to output.
        signed (bool): whether or not the output is signed or not.
    Returns:
        Bytes representing the given integer.
    """
    # Conversion from arguments to struct.pack format string.
    conversion = {(1, False): 'B', (1, True): 'b', (2, False): 'H', (2, True): 'h', (4, False): 'I', (4, True): 'i'}
    return pack('>' + conversion[(num_bytes, signed)], input_int)


def bytes_to_str(input_bytes):
    """
    Converts a sequence of bytes into the string representation.
    Args:
        input_bytes (bytes): Byte representation of an (ASCII) string.
    Returns:
        String representation.
    """
    s = input_bytes.decode('ascii', 'replace')
    return s


def bytes_to_hex(input_bytes):
    """
    Convenience function to turn bytes onto a nice hex string, because Python doesn't print the bytes properly.
    Args:
        input_bytes: Bytes to stringify.
    Returns:
        String representation of the bytes.
    """
    return r'\x' + r'\x'.join('{:02x}'.format(x) for x in input_bytes)


def bytes_to_uint(input_bytes):
    """
    Variable length convenience function to convert some number of bytes to an int.
    Args:
        input_bytes (bytes): Input bytes to convert.
    Returns:
        Integer.
    """
    num_bytes = len(input_bytes)
    mapping = {1: parse_uint8, 2: parse_uint16, 4: parse_uint32}
    f = mapping[num_bytes]
    return f(input_bytes)