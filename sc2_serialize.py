import sc2_parse as sc2p
from utils import serialize_int32, serialize_uint32, serialize_uint16, serialize_uint8, int_to_n_bits


def name_to_cnam(city_name):
    """
    Creates the CNAM segment contents, 32 bytes.
    Args:
        city_name (str): name of the city. If it is longer than 31 characters, it will be truncated.
    Returns:
        CNAM IFF segment bytes.
    """
    if len(city_name) > 31:
        city_name = city_name[: 31]
    data = bytearray(b'\x1F' + bytes(city_name, 'ascii') + b'\x00' * (31 - len(city_name)))
    return data


def serialize_misc(city):
    """
    Serialized the MISC segment, 4800 bytes.
    Args:
        city (City): city file to save the MISC contents of.
    Returns:
        Byte representation of the MISC segment.
    """
    # This is the offset of the section that's being parsed from MISC.
    parse_order = {
        '0x0000': 'FirstEntry',
        '0x0004': 'GameMode',
        '0x0008': 'Compass',
        '0x000c': 'baseYear',
        '0x0010': 'simCycle',
        '0x0014': 'TotalFunds',
        '0x0018': 'TotalBonds',
        '0x001c': 'GameLevel',
        '0x0020': 'CityStatus',
        '0x0024': 'CityValue',
        '0x0028': 'LandValue',
        '0x002c': 'CrimeCount',
        '0x0030': 'TrafficCount',
        '0x0034': 'Pollution',
        '0x0038': 'CityFame',
        '0x003c': 'Advertising',
        '0x0040': 'Garbage',
        '0x0044': 'WorkerPercent',
        '0x0048': 'WorkerHealth',
        '0x004c': 'WorkerEducate',
        '0x0050': 'NationalPop',
        '0x0054': 'NationalValue',
        '0x0058': 'NationalTax',
        '0x005c': 'NationalTrend',
        '0x0060': 'heat',
        '0x0064': 'wind',
        '0x0068': 'humid',
        '0x006c': 'weatherTrend',
        '0x0070': 'NewDisaster',
        '0x0074': 'oldResPop',
        '0x0078': 'Rewards',
        '0x007c': 'Population Graphs',
        '0x016c': 'Industry Graphs',
        '0x01f0': 'Tile Counts',
        '0x05f0': 'ZonePop|0',
        '0x05f4': 'ZonePop|1',
        '0x05f8': 'ZonePop|2',
        '0x05fc': 'ZonePop|3',
        '0x0600': 'ZonePop|4',
        '0x0604': 'ZonePop|5',
        '0x0608': 'ZonePop|6',
        '0x060c': 'ZonePop|7',
        '0x0610': 'Bonds',
        '0x06d8': 'Neighbours',
        '0x0718': 'Valve?|0',
        '0x071c': 'Valve?|1',
        '0x0720': 'Valve?|2',
        '0x0724': 'Valve?|3',
        '0x0728': 'Valve?|4',
        '0x072c': 'Valve?|5',
        '0x0730': 'Valve?|6',
        '0x0734': 'Valve?|7',
        '0x0738': 'gas_power',
        '0x073c': 'nuclear_power',
        '0x0740': 'solar_power',
        '0x0744': 'wind_power',
        '0x0748': 'microwave_power',
        '0x074c': 'fusion_power',
        '0x0750': 'airport',
        '0x0754': 'highways',
        '0x0758': 'buses',
        '0x075c': 'subways',
        '0x0760': 'water_treatment',
        '0x0764': 'desalinisation',
        '0x0768': 'plymouth',
        '0x076c': 'forest',
        '0x0770': 'darco',
        '0x0774': 'launch',
        '0x0778': 'highway_2',
        '0x077c': 'Budget',
        '0x0e3c': 'YearEnd',
        '0x0e40': 'GlobalSeaLevel',
        '0x0e44': 'terCoast',
        '0x0e48': 'terRiver',
        '0x0e4c': 'Military',
        '0x0e50': 'Paper List',
        '0x0ec8': 'News List',
        '0x0fa0': 'Ordinances',
        '0x0fa4': 'unemployed',
        '0x0fa8': 'Military Count',
        '0x0fe8': 'SubwayCnt',
        '0x0fec': 'GameSpeed',
        '0x0ff0': 'AutoBudget',
        '0x0ff4': 'AutoGo',
        '0x0ff8': 'UserSoundOn',
        '0x0ffc': 'UserMusicOn',
        '0x1000': 'NoDisasters',
        '0x1004': 'PaperDeliver',
        '0x1008': 'PaperExtra',
        '0x100c': 'PaperChoice',
        '0x1010': 'unknown128',
        '0x1014': 'Zoom',
        '0x1018': 'CityCentX',
        '0x101c': 'CityCentY',
        '0x1020': 'GlobalArcoPop',
        '0x1024': 'ConnectTiles',
        '0x1028': 'TeamsActive',
        '0x102c': 'TotalPop',
        '0x1030': 'IndustryBonus',
        '0x1034': 'PolluteBonus',
        '0x1038': 'oldArrest',
        '0x103c': 'PoliceBonus',
        '0x1040': 'DisasterObject',
        '0x1044': 'CurrentDisaster',
        '0x1048': 'GoDisaster',
        '0x104c': 'SewerBonus',
        '0x1050': 'Extra', }
    handle_special = ['Population Graphs', 'Industry Graphs', 'Tile Counts', 'Bonds', 'Neighbours', 'Budget',
                      'Military Count', 'Paper List', 'News List', 'Extra', 'Ordinances']
    handle_special += list(city.simulator_settings.keys()) + list(city.game_settings.keys()) + list(city.inventions.keys())
    output_bytes = bytearray(b"\x00" * 4800)
    for k, v in parse_order.items():
        offset = int(k, 16)
        if v not in handle_special:
            data = serialize_uint32(city.city_attributes[v])
            output_bytes[offset : offset + 4] = data
        elif v == 'Population Graphs':
            graph_values = [[a for a in g] for g in city.population_graphs.values()]
            data = interleave_data(graph_values)
            output_bytes[offset: offset + len(data)] = data
        elif v == 'Industry Graphs':
            graph_values = [[a for a in g] for g in city.industry_graphs.values()]
            data = interleave_data(graph_values)
            output_bytes[offset: offset + len(data)] = data
        elif v == 'Tile Counts':
            for building_count in city.building_count.values():
                data = serialize_uint32(building_count)
                output_bytes[offset : offset + 4] = data
                offset += 4
        elif v == 'Bonds':
            bonds_data = city.budget.serialize_bonds()
            output_bytes[offset : offset + len(bonds_data)] = bonds_data
        elif v == 'Ordinances':
            data = city.budget.serialize_ordinances()
            output_bytes[offset : offset + 4] = data
        elif v == 'Neighbours':
            for n in city.neighbor_info.values():
                for e in n.values():
                    data = serialize_uint32(e)
                    output_bytes[offset: offset + 4] = data
                    offset += 4
        elif v == 'Budget':
            budget_data = city.budget.serialize_budget()
            output_bytes[offset : offset + len(budget_data)] = budget_data
        elif v == 'Military Count':
            num_items = 16
            for x in range(num_items):
                data = serialize_uint32(city.city_attributes[f"Military Count|{x}"])
                output_bytes[offset: offset + 4] = data
                offset += 4
        elif v == 'Paper List':
            num_items = 6 * 5
            for x in range(num_items):
                data = serialize_uint32(city.city_attributes[f"Paper List|{x}"])
                output_bytes[offset: offset + 4] = data
                offset += 4
        elif v == 'News List':
            num_items = 9 * 6
            for x in range(num_items):
                data = serialize_uint32(city.city_attributes[f"News List|{x}"])
                output_bytes[offset: offset + 4] = data
                offset += 4
        elif v == 'Extra':
            for x in range(156):
                data = serialize_uint32(city.city_attributes[f"Extra|{x}"])
                output_bytes[offset: offset + 4] = data
                offset += 4
        elif v in list(city.simulator_settings.keys()):
            data = serialize_uint32(city.simulator_settings[v])
            output_bytes[offset: offset + 4] = data
        elif v in list(city.game_settings.keys()):
            data = serialize_uint32(city.game_settings[v])
            output_bytes[offset: offset + 4] = data
        elif v in list(city.inventions.keys()):
            data = serialize_uint32(city.inventions[v])
            output_bytes[offset: offset + 4] = data
        else:
            # Fallthrough, this should never, ever, be hit.
            print("MISC is missing something!", k, v)
    return output_bytes


def interleave_data(data):
    """
    Interleaves data for the Population and Industry Graphs.
    Each of the lists must be the same length.
    Args:
        data (list(list(int))): List of lists of the graph data.
    Returns:
        Bytearray containing the interleaved data.
    """
    # In hindsight, this is probably better served using zip().
    output = bytearray()
    for x in range(len(data[1])):
        for a in [serialize_int32(a[x]) for a in data]:
            output += bytearray(a)
    return output


def serialize_tile_data(city, which_tile):
    """

    Args:
        city (City): city to serialize the tiles from.
        which_tile (str): which tile type are we serializing?
            Possibile types: ALTM, XTER, XUND, XZON, XTXT, XBIT.
    Returns:
        Bytearray representation of the tiles.
    """
    tilelist = city.tilelist
    output_bytes = bytearray()
    for tile in tilelist.values():
        if which_tile == "ALTM":
            bit_string = ''
            bit_string += int_to_n_bits(tile.altidue_tunnel, 8)
            bit_string += int_to_n_bits(tile.is_water, 1)
            bit_string += int_to_n_bits(tile.altitude_unknown, 2)
            bit_string += int_to_n_bits(tile.altitude, 5)
            altidude_map = int(bit_string, 2)
            tile_data = serialize_uint16(altidude_map)
        elif which_tile == "XUND":
            tile_data = serialize_uint8(tile.underground)
        elif which_tile == "XTER":
            tile_data = serialize_uint8(tile.terrain)
        elif which_tile == "XZON":
            tile_data = serialize_uint8(tile.zone)
        elif which_tile == "XTXT":
            tile_data = serialize_uint8(tile.text_pointer)
        elif which_tile == "XBIT":
            flags = tile.bit_flags
            tile_data = serialize_uint8(int(flags))
        else:
            print("Tile data parsing failed.")
            tile_data = 0
        output_bytes += tile_data
    return output_bytes


def serialize_building_data(city):
    """
    Serializes building data. Assumes buildings are well-formed, etc.
    Args:
        city (City): city to pull buildings from.
    Returns:
        Byte representation of the buildings.
    """
    groundcover = city.groundcover
    networks = city.networks
    tilelist = city.tilelist
    output_bytes = ['b\x00' for x in range(city.city_size ** 2)]
    # Start with groundcover and networks.
    # Todo: make sure ordering on this works correctly.
    for k, v in networks.items():
        x, y = k
        offset = x * 128 + y
        data = serialize_uint8(v.building_id)
        output_bytes[offset] = data
    for k, v in groundcover.items():
        x, y = k
        offset = x * 128 + y
        data = serialize_uint8(v.building_id)
        output_bytes[offset] = data
    # Why not pull from the city.buildings here?
    # Because it doesn't store holes in buildings, but that are stores in the tilelist.
    for k, v in tilelist.items():
        x, y = k
        offset = x * 128 + y
        building = v.building
        if building is not None:
            data = serialize_uint8(building.building_id)
            output_bytes[offset] = data
    # t = b''.join(output_bytes)
    return output_bytes

