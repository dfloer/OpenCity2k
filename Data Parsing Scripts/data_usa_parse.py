import argparse
from collections import OrderedDict
import struct
import json


# Documentation for what this script is doing can be found at: https://github.com/dfloer/SC2k-docs/blob/master/text%20data%20spec.md#newspapers
# As the spec is incomplete, this parsing is also incomplete.

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
        (0x3d, '{CITYNAME}'),  # =
        (0x3e, '{TEAMNAME}'),  # >
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
        (0x7e, '{MAYORNAME}'),  # ~
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
        {
         0x00: "genweatherstory",
         0x01: "sciencestory",
         0x02: "foundingstory",
         0x03: "genpopulationstory",
         0x04: "invention2story",
         0x05: "inventionstory",
         0x06: "warstory",
         0x07: "businessstory",
         0x08: "sportsstory",
         0x09: "fedrateupstory",
         0x0a: "fedratedownstory",
         0x0b: "nationalpolitical",
         0x0c: "internationalstory",
         0x0d: "gendisasterstory",
         0x0e: "healthstory",
         0x0f: "localpoliticalstory",
         0x10: "highcrime",
         0x11: "hightraffic",
         0x12: "highpollution",
         0x13: "loweducation",
         0x14: "lowhealthcare",
         0x15: "highunemployment",
         0x16: "disasterfire",
         0x17: "disasterflood",
         0x18: "disasterplane",
         0x19: "disasterhelicopter",
         0x1a: "disastertornado",
         0x1b: "disastereqarthquake",
         0x1c: "disastermonster",
         0x1d: "disastermeltdown",
         0x1e: "disastermicrowave",
         0x1f: "disastervolcano",
         0x20: "disasterspill",
         0x21: "disastermajorspill",
         0x22: "disasterhurricane",
         0x23: "disasterriot",
         0x24: "oldpowerplant",
         0x25: "fundprison",
         0x26: "fundeducation",
         0x27: "fundtransit",
         0x28: "treeremoval",
         0x29: "gennewordinancestory",
         0x2a: "genrichopoinionstory",
         0x2b: "genrichgripestory",
         0x2c: "genopiniongripe",
         0x2d: "missimquestion",
         0x2e: "needpower",
         0x2f: "needroad",
         0x30: "needpolice",
         0x31: "needfire",
         0x32: "needwater",
         0x33: "needhospital",
         0x34: "needschool",
         0x35: "needseaport",
         0x36: "needairport",
         0x37: "needzoo",
         0x38: "stadiumneed",
         0x39: "needmarina",
         0x3a: "needpark",
         0x3b: "needseapoer",
         0x3c: "needconnections",
         0x3d: "lowcrime",
         0x3e: "highrating",
         0x3f: "lowpollution",
         0x40: "higheducation",
         0x41: "highhealth",
         0x42: "lowunemployment",
         0x43: "ordinance",
         0x44: "ordinanceopinion",
         0x45: "otherfire",
         0x46: "otherflood",
         0x47: "otherrailcrash",
         0x48: "othertornado",
         0x49: "otherearthquake",
         0x4A: "othermonster",
         0x4B: "foundingreaction",
         0x4C: "populationstory",
         0x4D: "reaction",
         0x4E: "missimanswer",
         0x4F: "gripeclosing",
         0x50: "weatherreport",
         0x51: "weatherprediction",
         0x52: "richopinion",
         0x53: "richgripe",
         0x54: "opiniongripe",
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
         0x63: "articlepointers",
         0x64: "ordinanceheadline",
         0x65: "weatherheadline",
         0x66: "populationheadline",
         0x67: "gripeheadline1",
         0x68: "gripeheadline2",
         0x69: "gripeheadline3",
         0x6A: "disasterheadline",
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
         0x7C: "observedverb",
         0x7D: "angerverb",
         0x7E: "presentverb1",
         0x7F: "want",
         0x80: "pastwant",
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
         0x99: "crimetype",
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
         0xA7: "ngo",
         0xA8: "room",
         0xA9: "numericposition",
         0xAA: "invention",
         0xAB: "invention2",
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
    parser.add_argument('-j', '--json', dest="json_file", help="json out file", required=False, default=False, nargs='?')
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
    # Add a check to make sure names aren't duplicated.
    bcv = bracket_contents.values()
    bcs = set([x for x in bracket_contents.values()])
    if len(bcs) != len(bcv):
        dupes = [x for x in bcs if list(bcv).count(x) != 1]
        raise AssertionError("Duplicate values in bracket_contents: " + ', '.join(dupes))

    idx_names = {
        1: "Group Start",
        2: "Group Count",
        3: "Token Pointer",
        4: "Token Data",
        5: "Story Power",
        6: "Story Decay"
    }

    # Read the index in reverse order. This means we always know where the last segment started, so calculating the length of the segment is easy.
    idx_contents = OrderedDict()
    last = len(raw_data)
    for idx in range(len(raw_idx), 0, -8):
        # because each is offset by 8B.
        idx_name = idx_names[idx // 8]
        idx_file_id = struct.unpack('<I', raw_idx[idx - 8: idx - 4])[0]
        if debug:
            print("IDX file_id: " + str(idx_file_id) + " = " + idx_name)
        idx_file_length = struct.unpack('<I', raw_idx[idx - 4: idx])[0]

        idx_contents[idx_name] = [idx_file_length, last]
        last = idx_file_length

    # Reverse the index metadata (so it's the right way around now) and pull segments from the raw data.
    sorted_idx_contents = OrderedDict(sorted(idx_contents.items()))
    data_segments = OrderedDict()
    for segment_id, segment_offsets in sorted_idx_contents.items():
        data_segments[segment_id] = raw_data[segment_offsets[0]: segment_offsets[1]]
        if debug:
            debug_message = "{}: [{}, {}], len={}".format(segment_id, hex(segment_offsets[0]), hex(segment_offsets[1]), len(data_segments[segment_id]))
            print(debug_message)


    group_start_data = data_segments["Group Start"]
    group_count_data = data_segments["Group Count"]
    groups = parse_groups(group_start_data, group_count_data)
    pointer_data = data_segments["Token Pointer"]
    pointers = parse_pointers(pointer_data)

    text_data = pointer_data = data_segments["Token Data"]
    parsed_text_data, group_names = parse_text(text_data, pointers, groups, token_lookup_table, bracket_contents, debug)
    return parsed_text_data, group_names


def parse_pointers(pointer_data):
    """
    Parses the pointer segment of the data file and returns the pointers. Each is a 4B int.
    Args:
        pointer_data (bytes): Raw data to parse.
    Returns:
        list: List ot pointers
    """
    pointers = []
    for idx in range(0, len(pointer_data), 4):
        pointers += [struct.unpack('>I', pointer_data[idx : idx + 4])[0] ]
    return pointers


def parse_groups(group_start, group_count):
    """
    Tokens are stored as groups
    Args:
        group_start ([type]): [description]
        group_count ([type]): [description]

    Returns:
        [type]: [description]
    """
    grp_start = []
    grp_count = []
    assert len(group_start) == len(group_count)
    for idx in range(0, len(group_start), 2):
        grp_start += [struct.unpack('>H', group_start[idx : idx + 2])[0]]
        grp_count += [struct.unpack('>H', group_count[idx : idx + 2])[0]]
    res = OrderedDict((k, v) for k, v in zip(grp_start, grp_count) if k != 0 or v != 0)
    return res


def parse_text(raw, pointers, groups, lookup, bracket, debug):
    """
    Handles actually turning the compressed data back into useful text. Right now puts placeholder "pointers" to the various madlibs-esque words/short phrases etc. to fill in. Full details in data_usa.dat file spec.
    Args:
        raw (bytes): complete data_usa.dat in raw, uncompressed form.
        pointers (list): List of pointers to each token.
        groups (dict): Dictionary of {start_offset: token count} values.
        lookup (dict): lookup table for token values.
        bracket (dict): lookup table for escaped token values.
        debug (bool): if true, print extra (a lot extra!) debug output.
    Returns:
        A dictionary of uncompressed data, with the keys being the same as the segments passed in.
    """
    tokens = []
    # Parse raw data into tokens, based on pointers from the token pointers.
    for i, p in enumerate(pointers):
        if p == 0:
            continue
        next_p = pointers[i + 1]
        entry = raw[p : next_p]
        # If we're on the last entry, there isn't a next pointer, so we want to take the rest of the list.
        if next_p == 0:
            entry = raw[p : ]
        if debug:
            print("i", i, "p", p, "np", next_p, "len", len(entry))

        entry = entry[: -1]
        if debug:
            print(entry)

        token_idx = 0
        parsed_chunk = ''
        while token_idx < len(entry):
            token = entry[token_idx]
            lookup_idx = int(token)
            token_value = lookup.get(lookup_idx, hex(token))
            if token_value == '\\':
                token_value = ''  # Handle escape characters from the file.
            if token_value in ('*', '[', '^', '@', '&') and (token_idx + 1) != len(entry):
                token_idx += 1
                bracket_arg = int(entry[token_idx])
                if token_value in ('*', '@', '^', '&'):
                    token_extra = token_value
                else:
                    token_extra = ''
                if bracket_arg in bracket.keys():
                    token_value = '{' + token_extra + bracket[bracket_arg].upper() + '}'
                elif bracket_arg == 0x20:
                    token_value = '0x20'  # the '&' character is used as an escape for certain tokens, so it has it's own sequence.
                else:
                    token_value = '{' + token_extra + hex(bracket_arg) + '}'
            parsed_chunk += token_value
            token_idx += 1
        tokens += [parsed_chunk]

    # Arrange the tokens into their groups.
    grouped_tokens = OrderedDict()
    for gidx, cnt in groups.items():
        gidx = gidx - 1
        end = gidx + cnt
        grouped_tokens[gidx] = tokens[gidx : end]

    # Find the name associated with a group.
    # This is a bit weird because we want to match with the list of bracket escaped tokens in reverse.
    # Which means we need to un-reverse to get the correct ordering back.
    group_names = OrderedDict()
    kr = list(reversed(list(grouped_tokens)))
    # offset = 0x4B
    offset = 0
    end = 0xCE
    ids = [x for x in range(end - offset, 0, -1)]
    for idx, x in enumerate(kr):
        r_idx = abs(-end + idx)
        if idx <= len(ids):
            val = bracket.get(r_idx, hex(r_idx))
            group_names[x] = bracket.get(r_idx, val)
        elif idx > end - offset:
            group_names[x] = hex(r_idx)

    return grouped_tokens, group_names


def generate_output(grouped_tokens, group_names):
    ls = ''
    for k, v in grouped_tokens.items():
        n = group_names.get(k, '')
        name = ''
        if n:
            name = " (" + n + ")"
        ls += "``````````````````````````\nGroup ID: " + str(k) + name + '\n'
        for i, e in enumerate(v):
            ls += "token " + str(i) + ": " + e + "\n\n"
    return ls

def output_as_json(grouped_tokens, group_names):
    out = {group_names[k]: v for k, v in grouped_tokens.items()}
    return json.dumps(out)

if __name__ == "__main__":
    options = parse_command_line()

    input_path = options.input_file
    output_path = options.output_file
    debug = options.debug
    output_path_json = options.json_file
    files = ["DATA_USA.DAT", "DATA_USA.IDX"]

    with open(input_path + files[0], 'rb') as f:
        raw_unparsed_data = f.read()
    with open(input_path + files[1], 'rb') as f:
        raw_idx = f.read()

    if debug is None:
        debug = True

    output, names = parse_data_usa(raw_unparsed_data, raw_idx, debug)
    with open(output_path, 'w') as f:
        print("output written to: ", str(output_path))
        f.write(generate_output(output, names))

    if output_path_json:
        with open(output_path_json, 'w') as f:
            print("output written to: ", str(output_path_json))
            f.write(output_as_json(output, names))
