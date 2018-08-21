#!/usr/bin/env python
import sys
sys.path.append('..')  # Only way I could get an import from the parent directory working.
import sc2_iff_parse as sc2p
from collections import OrderedDict, namedtuple
import argparse

# The documentation on what this is doing is found at: https://github.com/dfloer/SC2k-docs/blob/master/text%20data%20spec.md


def parse_text_usa(raw_file, raw_index_file):
    """
    Splits the TEXT_USA.DAT file based on the TEXT_USA.IDX and creates an dictionary containing each segments id, offset, raw data and cleaned and formatted (as it would display in the game) string version of the raw data.
    Args:
        raw_file (bytes): raw bytes representing the TEXT_USA.DAT file.
        raw_index_file (bytes): raw bytes representing the TEXT_USA.IDX file.
    Returns:
        A dictinary where the key is the id from the .IDX file and the values are the offset, raw data dump and nice string output.
    """
    text = namedtuple("text", ["offset", "raw_data", "string"])
    index_dict = OrderedDict()
    text_data = OrderedDict()

    for idx in range(0, len(raw_index_file), 8):
        segment_id = int.from_bytes(raw_index_file[idx : idx + 4], byteorder='little')
        segment_length = int.from_bytes(raw_index_file[idx + 4 : idx + 8], byteorder='little')
        index_dict[segment_id] = segment_length

    end = len(raw_file)
    offsets = []
    for value in index_dict.values():
        offsets.extend([value])
    offsets.extend([end])
    lengths = [offsets[x] - offsets[x - 1] for x in range(1, len(index_dict) + 1)]

    idx = 0
    for segment_id, segment_offset in index_dict.items():
        length = lengths[idx]
        idx += 1
        data = raw_file[segment_offset : segment_offset + length]
        data_string = data.decode(encoding='ascii', errors='ignore')
        entry = text(segment_offset, data, data_string)
        text_data[segment_id] = entry
    return text_data


def save_text(output_file, text):
    """
    Saves the generated text to the given output, with a numeric header denoting the ID in the file.
    Args:
        output_file (bytes): full path to file to save clean strings to.
        text (str): string contents to write to output file.
    """
    with open(output_file, 'w') as f:
        for segment_id, segment_text in text.items():
            f.write(str(segment_id) + ":\n" + segment_text.string + "\n")


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--data', dest="input_file", help="path to TEXT_USA.DAT", metavar="FILE", required="true")
    parser.add_argument('-i', '--index', dest="index_file", help="path to TEXT_USA.IDX", metavar="FILE", required="true")
    parser.add_argument('-t', '--text', dest="output_file", help="text file with strings and IDs.", metavar="FILE", required=False)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    options = parse_command_line()

    try:
        raw_file = sc2p.open_file(options.input_file)
    except Exception as e:
            print("Reading TEXT_USA.DAT failed with error:\n" + str(e))
            raise
    try:
        raw_index_file = sc2p.open_file(options.index_file)
    except Exception as e:
        print("Reading TEXT_USA.IDX failed with error:\n" + str(e))
        raise

    text_output = parse_text_usa(raw_file, raw_index_file)

    if options.output_file:
        try:
            save_text(options.output_file, text_output)
        except Exception as e:
            print("Writing text failed with error:\n" + str(e))
            raise
    else:
        for k, v in text_output.items():
            print(str(k) + ":\n", v.string)