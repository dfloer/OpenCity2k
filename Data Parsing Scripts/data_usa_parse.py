import argparse
from collections import OrderedDict
import struct


# Documentation for what this script is doing can be found at: https://github.com/dfloer/SC2k-docs/blob/master/text%20data%20spec.md#newspapers
# As the spec is incomplete, this parsing is also incomplete.


def parse_command_line():
    """
    Set up command line arguments.
    Args:
        None.
    Returns:
        Argparse object for setting up command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest="input_file", help="path to directory containing DATA_USA.DAT and DATA_USA.IDX", metavar="PATH", required=True)
    parser.add_argument('-o', '--output', dest="output_file", help="out file", metavar="FILE", required=True)
    parser.add_argument('-d', '--debug', dest="debug", help="Debug printing enables.", required=False, default=False, nargs='?')
    args = parser.parse_args()
    return args


def parse_data_usa(raw_data, raw_idx, debug):
    """
    Uncompressed and parses the DATA_USA.DAT newspaper file into a more usable form. Full details in DATA_USA.DAT format spec doc at: https://github.com/dfloer/SC2k-docs/blob/master/text%20data%20spec.md#newspapers
    Uses a token lookup table to replace various single byte tokens with their ASCII values and another lookup table for "bracket" escaped values.
    Args:
        raw_data (bytes): complete data_usa.dat in raw, uncompressed form.
        raw_idx (bytes): complete data_usa.dat in raw form.
        debug (bool): if true, print extra (a lot extra!) debug output.
    Returns:
        A list of single item dictionaries of the form {key given in the index file: parsed/uncompressed string representation of the data}.
    """
    token_lookup_table = OrderedDict([
        (0x0, 'None'),
        (0x01, 'th'),
        (0x02, 'in'),
        (0x03, 're'),
        (0x04, 'to'),
        (0x05, 'an'),
        (0x06, 'at'),
        (0x07, 'er'),
        (0x08, 'st'),
        (0x09, 'en'),
        (0x0a, 'on'),
        (0x0b, 'of'),
        (0x0c, 'te'),
        (0x0d, 'ed'),
        (0x0e, 'ar'),
        (0x0f, 'is'),
        (0x10, 'ng'),
        (0x11, 'me'),
        (0x12, 'co'),
        (0x13, 'ou'),
        (0x14, 'al'),
        (0x15, 'ti'),
        (0x16, 'es'),
        (0x17, 'll'),
        (0x18, 'he'),
        (0x19, 'ha'),
        (0x1a, 'it'),
        (0x1b, 'ca'),
        (0x1c, 've'),
        (0x1d, 'fo'),
        (0x1e, 'de'),
        (0x1f, 'be'),
        (0x20, ' '),
        (0x21, '!'),
        (0x22, '"'),
        (0x23, '#'),
        (0x24, '$'),
        (0x25, '%'),
        (0x26, '&'),
        (0x27, "'"),
        (0x28, '('),
        (0x29, ')'),
        (0x2a, '*'),
        (0x2b, '+'),
        (0x2c, ','),
        (0x2d, '-'),
        (0x2e, '.'),
        (0x2f, '/'),
        (0x30, '0'),
        (0x31, '1'),
        (0x32, '2'),
        (0x33, '3'),
        (0x34, '4'),
        (0x35, '5'),
        (0x36, '6'),
        (0x37, '7'),
        (0x38, '8'),
        (0x39, '9'),
        (0x3a, ':'),
        (0x3b, ';'),
        (0x3c, '<'),
        (0x3d, '=CITYNAME'),  # =
        (0x3e, '>TEAMNAME'),  # >
        (0x3f, '?'),
        (0x40, '@'),
        (0x41, 'A'),
        (0x42, 'B'),
        (0x43, 'C'),
        (0x44, 'D'),
        (0x45, 'E'),
        (0x46, 'F'),
        (0x47, 'G'),
        (0x48, 'H'),
        (0x49, 'I'),
        (0x4a, 'J'),
        (0x4b, 'K'),
        (0x4c, 'L'),
        (0x4d, 'M'),
        (0x4e, 'N'),
        (0x4f, 'O'),
        (0x50, 'P'),
        (0x51, 'Q'),
        (0x52, 'R'),
        (0x53, 'S'),
        (0x54, 'T'),
        (0x55, 'U'),
        (0x56, 'V'),
        (0x57, 'W'),
        (0x58, 'X'),
        (0x59, 'Y'),
        (0x5a, 'Z'),
        (0x5b, '['),
        (0x5c, '\\'),
        (0x5d, ']'),
        (0x5e, '^'),
        (0x5f, '_'),
        (0x60, '`'),
        (0x61, 'a'),
        (0x62, 'b'),
        (0x63, 'c'),
        (0x64, 'd'),
        (0x65, 'e'),
        (0x66, 'f'),
        (0x67, 'g'),
        (0x68, 'h'),
        (0x69, 'i'),
        (0x6a, 'j'),
        (0x6b, 'k'),
        (0x6c, 'l'),
        (0x6d, 'm'),
        (0x6e, 'n'),
        (0x6f, 'o'),
        (0x70, 'p'),
        (0x71, 'q'),
        (0x72, 'r'),
        (0x73, 's'),
        (0x74, 't'),
        (0x75, 'u'),
        (0x76, 'v'),
        (0x77, 'w'),
        (0x78, 'x'),
        (0x79, 'y'),
        (0x7a, 'z'),
        (0x7b, '{'),
        (0x7c, '|'),
        (0x7d, '}'),
        (0x7e, '~MAYORNAME'),  # ~
        (0x7f, 'wi'),
        (0x80, ''),
        (0x81, ''),
        (0x82, ''),
        (0x83, ''),
        (0x84, ''),
        (0x85, ''),
        (0x86, ''),
        (0x87, ''),
        (0x88, ''),
        (0x89, ''),
        (0x8a, ''),
        (0x8b, ''),
        (0x8c, ''),
        (0x8d, ''),
        (0x8e, ''),
        (0x8f, ''),
        (0x90, ''),
        (0x91, ''),
        (0x92, ''),
        (0x93, ''),
        (0x94, ''),
        (0x95, ''),
        (0x96, ''),
        (0x97, ''),
        (0x98, ''),
        (0x99, ''),
        (0x9a, ''),
        (0x9b, ''),
        (0x9c, ''),
        (0x9d, ''),
        (0x9e, 'le'),
        (0x9f, 'or'),
        (0xa0, ''),
        (0xa1, ''),
        (0xa2, ''),
        (0xa3, ''),
        (0xa4, ''),
        (0xa5, ''),
        (0xa6, ''),
        (0xa7, ''),
        (0xa8, ''),
        (0xa9, 'ma'),
        (0xaa, 'li'),
        (0xab, 'we'),
        (0xac, 'ne'),
        (0xad, ''),
        (0xae, 'se'),
        (0xaf, 'nt'),
        (0xb0, 'wa'),
        (0xb1, 'wh'),
        (0xb2, 'pr'),
        (0xb3, 'si'),
        (0xb4, 'as'),
        (0xb5, ''),
        (0xb6, ''),
        (0xb7, ''),
        (0xb8, 'nd'),
        (0xb9, 'po'),
        (0xba, 'la'),
        (0xbb, 'no'),
        (0xbc, 'ce'),
        (0xbd, 'fi'),
        (0xbe, 'yo'),
        (0xbf, 'do'),
        (0xc0, 'di'),
        (0xc1, 'mo'),
        (0xc2, 'bu'),
        (0xc3, 'ho'),
        (0xc4, 'ea'),
        (0xc5, 'un'),
        (0xc6, ''),
        (0xc7, ''),
        (0xc8, 'io'),
        (0xc9, 'pa'),
        (0xca, 'ra'),
        (0xcb, 'ke'),
        (0xcc, 'lo'),
        (0xcd, 'ly'),
        (0xce, 'ri'),
        (0xcf, 'sh'),
        (0xd0, ''),
        (0xd1, ''),
        (0xd2, ''),
        (0xd3, ''),
        (0xd4, ''),
        (0xd5, ''),
        (0xd6, ''),
        (0xd7, ''),
        (0xd8, ''),
        (0xd9, 'pe'),
        (0xda, 'ch'),
        (0xdb, 'tr'),
        (0xdc, 'ci'),
        (0xdd, 'hi'),
        (0xde, ''),
        (0xdf, 'so'),
        (0xe0, ''),
        (0xe1, ''),
        (0xe2, ''),
        (0xe3, ''),
        (0xe4, ''),
        (0xe5, ''),
        (0xe6, ''),
        (0xe7, ''),
        (0xe8, ''),
        (0xe9, ''),
        (0xea, ''),
        (0xeb, ''),
        (0xec, ''),
        (0xed, ''),
        (0xee, 'su'),
        (0xef, 'rt'),
        (0xf0, 'ta'),
        (0xf1, 'ge'),
        (0xf2, 'rs'),
        (0xf3, 'ow'),
        (0xf4, 'us'),
        (0xf5, 'ss'),
        (0xf6, 'sp'),
        (0xf7, 'ac'),
        (0xf8, 'il'),
        (0xf9, 'ic'),
        (0xfa, 'pl'),
        (0xfb, 'fe'),
        (0xfc, 'wo'),
        (0xfd, 'da'),
        (0xfe, 'ai'),
        (0xff, 'ur'), ])

    bracket_contents = \
        {0x4B: "foundingreaction",
         0x4D: "reaction",
         0x4E: "missimanswer",
         0x4F: "gripeclosing",
         0x55: "gripe1",
         0x56: "gripe2",
         0x57: "gripe3",
         0x58: "gripe4",
         0x59: "gripe5",
         0x5A: "gripe6",
         0x5B: "gripe7",
         0x5C: "traffic",
         0x5D: "pollution",
         0x5E: "crime",
         0x5F: "taxes",
         0x60: "employment",
         0x61: "education",
         0x62: "health",
         0x6B: "destroyverb",
         0x6C: "creationverb",
         0x6D: "pastcreationverb",
         0x6E: "fireverb",
         0x6F: "increase",
         0x70: "verb1",
         0x71: "verb2",
         0x72: "futureverb",
         0x73: "makeverb",
         0x74: "pastmakeverb",
         0x75: "makenoun",
         0x76: "response",
         0x77: "utterance",
         0x78: "feeling",
         0x79: "scareverb",
         0x7A: "violentverb",
         0x7B: "pastviolentverb",
         0x7C: "verb1",
         0x7D: "verb2",
         0x7E: "presemtverb1",
         0x7F: "help",
         0x80: "pasthelp",
         0x81: "negativeverb",
         0x82: "pastverb",
         0x83: "thingdescriptor",
         0x84: "adjective",
         0x85: "adverb1",
         0x86: "adverb2",
         0x87: "time",
         0x88: "negativefeeling",
         0x89: "animal",
         0x8A: "negativeadjective",
         0x8B: "bodypart",
         0x8C: "disaster",
         0x8D: "bignumber",
         0x8E: "locals",
         0x8F: "localgov",
         0x90: "landmark",
         0x91: "othercity",
         0x92: "localcity",
         0x93: "response3",
         0x94: "shortsaying",
         0x95: "action1",
         0x96: "action2",
         0x97: "country",
         0x98: "criminal",
         0x99: "crime",
         0x9A: "infrastructure",
         0x9B: "direction",
         0x9C: "illness2",
         0x9D: "exclamation",
         0x9E: "expert",
         0x9F: "emotion",
         0xA0: "compete",
         0xA1: "malename",
         0xA2: "femalename",
         0xA3: "foreignfirstname",
         0xA4: "foreignlastname",
         0xA5: "2xforeignname",
         0xA6: "name",
         0xA7: "NGO",
         0xA8: "room",
         0xA9: "numericposition",
         0xAA: "invention",
         0xAB: "invetion2",
         0xAC: "politicalissue",
         0xAD: "product",
         0xAE: "size",
         0xAF: "title",
         0xB0: "lname",
         0xB1: "legalthing",
         0xB2: "llama",
         0xB3: "illness",
         0xB4: "amount",
         0xB5: "importantperson",
         0xB6: "moneything",
         0xB7: "moneyevent",
         0xB8: "money",
         0xB9: "month",
         0xBA: "positive",
         0xBB: "numberword",
         0xBC: "noun",
         0xBD: "job",
         0xBE: "territory",
         0xBF: "powertype",
         0xC0: "relative",
         0xC1: "smalladjective",
         0xC2: "sport",
         0xC3: "injury",
         0xC4: "sportscore",
         0xC5: "teamname",
         0xC6: "business",
         0xC7: "location",
         0xC8: "research",
         0xC9: "badthing",
         0xCA: "waterbody",
         0xCB: "group",
         0xCC: "governmentthing",
         0xCD: "weathercondition",
         0xCE: "weekday", }

    # Read the index in reverse order. This means we always know where the last segment started, so calculating the length of the segment is easy.
    idx_contents = OrderedDict()
    last = len(raw_data)
    for idx in range(len(raw_idx), 0, -8):
        idx_file_id = struct.unpack('<I', raw_idx[idx - 8: idx - 4])[0]
        idx_file_length = struct.unpack('<I', raw_idx[idx - 4: idx])[0]
        idx_contents[idx_file_id] = [idx_file_length, last]
        last = idx_file_length

    # Reverse the index metadata (so it's the right way around now) and pull segments from the raw data.
    sorted_idx_contents = OrderedDict(sorted(idx_contents.items()))
    data_segments = OrderedDict()
    for segment_id, segment_offsets in sorted_idx_contents.items():
        data_segments[segment_id] = raw_data[segment_offsets[0]: segment_offsets[1]]
        if debug:
            debug_message = "{}: [{}, {}], len={}".format(hex(segment_id), hex(segment_offsets[0]), hex(segment_offsets[1]), len(data_segments[segment_id]))
            print(debug_message)

    # Uncompress raw segments.
    parsed_data = OrderedDict()
    for segment_id, segment_data in data_segments.items():
        parsed_data[segment_id] = parse_chunk(segment_data, token_lookup_table, bracket_contents, debug)

    if debug:
        for k, v in parsed_data.items():
            print(
                "\n\n----------------\n " + hex(k) + " : " + str(len(v)) + '/' + hex(len(v)) + "\n----------------\n\n")
            s = ''
            for kk, vv in v.items():
                s += "({}: '{}'), ".format(hex(kk), vv)
            print(s)
    output = [{segment_id: segment_data} for segment_id, segment_data in parsed_data.items()]
    return output


def parse_chunk(raw_data, token_lookup_table, bracket_contents, debug):
    """
    Handles actually turning the compressed data back into useful text. Right now puts placeholder "pointers" to the various madlibs-esque words/short phrases etc. to fill in. Full details in data_usa.dat file spec.
    Args:
        raw_data (bytes): complete data_usa.dat in raw, uncompressed form.
        token_lookup_table (dict): lookup table for token values.
        bracket_contents (dict): lookup table for escaped token values.
        debug (bool): if true, print extra (a lot extra!) debug output.
    Returns:
        A dictionary of uncompressed data, with the keys being the same as the segments passed in.
    """
    output_dict = OrderedDict()
    for idx, entry in enumerate(raw_data.split(b'\x00')):
        parsed_chunk = ''

        token_idx = 0
        while token_idx < len(entry):
            token = entry[token_idx]
            lookup_idx = int(token)
            token_value = token_lookup_table[lookup_idx]
            if token_value == '':
                token_value = '[{}]'.format(hex(token))
            if token_value == '\\':
                token_value = ''  # Handle escape characters from the file.

            if token_value in ('*', '[', '^', '@', '&') and (token_idx + 1) != len(entry):
                token_idx += 1
                bracket_arg = int(entry[token_idx])
                if token_value in ('@', '^', '&'):
                    token_extra = token_value
                else:
                    token_extra = ''
                if bracket_arg in bracket_contents.keys():
                    token_value = '[' + token_extra + bracket_contents[bracket_arg].upper() + ']'
                elif bracket_arg == 0x20:
                    token_value = '& '  # the '&' character is used as an escape for certain tokens, so it has it's own sequence.
                else:
                    token_value = '[' + token_extra + hex(bracket_arg) + ']'

            parsed_chunk += token_value
            token_idx += 1

        if debug:
            print("index:", idx)
            raw = ''.join(['\\' + hex(c) for c in entry])
            print("raw:", raw)
            print("raw+:", entry)
            print("parsed:", parsed_chunk)
            print("----------------")
        output_dict[idx] = parsed_chunk
    return output_dict


if __name__ == "__main__":
    options = parse_command_line()

    input_path = options.input_file
    output_path = options.output_file
    debug = options.debug
    files = ["DATA_USA.DAT", "DATA_USA.IDX"]

    with open(input_path + files[0], 'rb') as f:
        raw_unparsed_data = f.read()
    with open(input_path + files[1], 'rb') as f:
        raw_idx = f.read()

    if debug is None:
        debug = True

    output = parse_data_usa(raw_unparsed_data, raw_idx, debug)
    with open(output_path, 'w') as f:
        for x in output:
            for k, v in x.items():
                segment_break = "----------------\n{}: {}/{} \n----------------\n".format(hex(k), hex(len(v)),
                                                                                          str(len(v)))
                f.write(segment_break)
                for line in v.values():
                    if line != '':
                        f.write(line)
                        f.write('\n')