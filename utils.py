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


def serialize_int32(integer):
    """
    Serialized an integer into a 4-bytes int32.
    Args:
        integer (int): Integer to turn into bytes.
    Returns:
        Byte representation
    """
    return pack('>i', integer)


def parse_uint32(unparsed_bytes):
    """
    Parses 4 bytes into a big endian unsigned integer.
    Args:
        unparsed_bytes (bytes): 4 bytes representing the int.
    Returns:
        Integer representation.
    """
    return unpack('>I', unparsed_bytes)[0]


def serialize_uint32(integer):
    """
    Serialized an integer into a 4-bytes unsigned int32.
    Args:
        integer (int): Integer to turn into bytes.
    Returns:
        Byte representation
    """
    return pack('>I', integer)


def parse_uint16(unparsed_bytes):
    """
    Parses 2 bytes into a big endian unsigned integer.
    Args:
        unparsed_bytes (bytes): 2 bytes representing the int.
    Returns:
        Integer representation.
    """
    return unpack('>H', unparsed_bytes)[0]


def serialize_uint16(integer):
    """
    PSerialized an integer into a 2-byte unsigned int.
    Args:
        integer (int): Integer to turn into bytes.
    Returns:
        Byte representation.
    """
    return pack('>H', integer)


def parse_uint8(unparsed_bytes):
    """
    Parses 1 byte into a big endian signed integer.
    Args:
        unparsed_bytes (bytes): 1 bytes representing the int.
    Returns:
        Integer representation.
    """
    return unpack('>B', unparsed_bytes)[0]


def serialize_uint8(integer):
    """
    PSerialized an integer into a 2-byte unsigned int.
    Args:
        integer (int): Integer to turn into bytes.
    Returns:
        Byte representation.
    """
    return pack('>B', integer)


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

def uint_to_bytes(uint, num_bytes):
    """
    Variable length convenience function to convert some number of bytes to an int.
    Args:
        input_bytes (bytes): Input bytes to convert.
    Returns:
        Integer.
    """
    mapping = {1: serialize_uint8, 2: serialize_uint16, 4: serialize_uint32}
    f = mapping[num_bytes]
    return f(uint)


def bytes_to_int32s(input_bytes):
    """
    Turns a sequence of bytes (must be a multiple of 4) into a list of integers.
    Args:
        input_bytes (bytes): bytes to convert
    Returns:
        List of converted signed integers.
    """
    res = []
    for offset in range(0, len(input_bytes), 4):
        res += [parse_int32(input_bytes[offset : offset +4])]
    return res


def trim_cstring(input_bytes):
    """
    SC2k data files have a lot of garbage in them after the end of a cstring, so this trims those bytes and returns the trimmed string.
    Args:
        input_bytes (bytes): dirty string
    Returns:
        Clean string.
    """
    clean_string = ""
    for char in input_bytes:
        if char == 0x00:
            break
        clean_string += chr(char)
    return clean_string


def int_to_n_bits(integer, num_bits):
    """
    Converts an int to a a bitstring of a specific number of bits.
    If it's larger, it'll get truncated.
    Args:
        integer (int): number to convert.
        num_bits (int): number of bits to maye the output string.
    Returns:
        A binary string representation of the integer.
    """
    return f"{integer:0{num_bits}b}"


"""
The follow utilities are ones that have been solely used for reverse engineering and documentation efforts and aren't use anywhere in the game file parsing.
"""

def data_in_many_formats(raw_data):
    """
    Prints the input data and prints it in as many formats as possible.
    Args:
        raw_data (bytes): input data.
    """
    lr = len(raw_data)
    print("raw len:", lr)
    print("raw")
    print([hex(x) for x in raw_data])
    print("int8")
    res = [x for x in raw_data]
    print(res)
    print("ascii")
    res = [chr(x) for x in raw_data]
    print(res)
    nm = {"int16": 'h', "int32": 'i', "uint16": 'H', "uint32": 'I', "float16": 'e', "float32": 'f', "float64": 'd'}
    em = {'b': '>', 'l': '<'}

    m = {ek + " " + nk: ev + nv for nk, nv in nm.items() for ek, ev in em.items()}
    for name, fmt in m.items():
        sz = int(''.join([x for x in name if x.isdigit()])) // 8
        print(name)
        res = try_parse(fmt, raw_data, sz)
        print(res)

def try_parse(fmt, data, size):
    try:
        res = [unpack(fmt, data[x : x + size])[0] for x in range(0, len(data), size)]
    except:
        res = "Error"
    return res


def article_metadata_markdown(d):
    """
    A simple function to take the values from bracket_replace and make them into a nice markdown table.
    """
    articles = (0x00, 0x43)
    complex_tokens = (0x43, 0x6B)
    simple_tokens = (0x6B, 0xCE)
    header = ("Value", "Group")

    x = {k: d[k] for k in range(*articles)}
    generate_table(x, header, 4)
    print("\n\n")
    x = {k: d[k] for k in range(*complex_tokens)}
    generate_table(x, header, 4)
    print("\n\n")
    x = {k: d[k] for k in range(*simple_tokens)}
    generate_table(x, header, 4)


def generate_table(d, h, c, ju='<'):
    """
    Turns a dict into a c * 2 column wide table and prints it.
    Args:
        d (dict): dict to make into a table.
        h (tuple): ("header, "header1") values.
        c (int): How many cols of values. 4 = 8 total columns.
        ju (str, optional): Justtification, as per f-string standard. Defaults to < (left).
    """
    l = len(d)
    sz = round(l / c)
    v_max = max(max([len(a) for a in d.values()]), len(h[1]))
    k_max = max(4, len(h[0]))
    for i in range(4):
        print(f"| {h[0]:{ju}{k_max}} | {h[1]:{ju}{v_max}} ", end='')
    print('|')
    dash = '-'
    for i in range(4):
        print(f"|-{'':{dash}{ju}{k_max}}-|-{'':{dash}{ju}{v_max}}-", end='')
    print('|')
    for i in range(min(d.keys()), min(d.keys()) + sz):
        for j in range(4):
            k = i + j * sz
            kh = f"0x{k:02X}"
            if k in d:
                print(f"| {kh:{ju}{k_max}} | {d[k]:{ju}{v_max}} ", end='')
            else:
                print(f"| {'':{ju}{k_max}} | {'':{ju}{v_max}} ", end='')
        print('|')