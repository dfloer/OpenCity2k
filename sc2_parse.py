import sc2_iff_parse as sc2p
import itertools
import collections
from utils import parse_int32
import argparse
import os.path
import Data.buildings as buildings


class City:
    """
    Class to store all of a city information, including buildings and all other tile contents, MISC city data, minimaps, etc.
    Also handles serializing a city back out to a complaint .sc2 (or .scn file).
    """
    # constants
    _graph_window_graphs = ['City Size', 'Residents', 'Commerce', 'Industry', 'Traffic', 'Pollution', 'Value',
                            'Crime', 'Power %', 'Water %', 'Health', 'Education', 'Unemployment', 'GNP', "Nat'n Pop.",
                            'Fed Rate']
    _population_graph_names = ['population_percent', 'health_le', 'education_eq']
    _industry_graph_names = ['industrial_ratios', 'industrial_tax_rate', 'industrial_demand']
    _simulator_setting_names = ['YearEnd', 'GlobalSeaLevel', 'terCoast', 'terRiver', 'Military', 'Zoom', 'Compass',
                                'CityCentX', 'CityCentY']
    _game_setting_names = ['GameSpeed', 'AutoBudget', 'AutoGo', 'UserSoundOn', 'UserMusicOn', 'NoDisasters']
    _invention_names = ['gas_power', 'nuclear_power', 'solar_power', 'wind_power', 'microwave_power', 'fusion_power',
                        'airport', 'highways', 'buses', 'subways', 'water_treatment', 'desalinisation', 'plymouth',
                        'forest', 'darco', 'launch', 'highway_2']
    def __init__(self):
        self.city_name = ""
        # self.tilelist = []
        self.xthg = {}
        self.labels = {}
        self.microsim_state = {}
        self.graph_data = {}
        self.buildings = {}
        self.city_size = 128

        # temporary
        self.misc_hack = bytearray()
        self.graph_data_hack = bytearray()
        self.labels_hack = bytearray()

        # Stuff from Misc
        self.city_attributes = {}
        self.budget = None
        self.ordinances = [0] * 20
        self.neighbor_info = {}
        self.building_count = []
        self.simulator_settings = {}
        self.inventions = {}
        self.population_graphs = {}
        self.industry_graphs = {}
        self.simulator_settings = {x: None for x in self._simulator_setting_names}
        self.game_settings = {x: None for x in self._game_setting_names}
        self.inventions = {x: None for x in self._invention_names}

        # Optional Scenario stuff
        self.is_scenario = False
        self.scenario_text = ''
        self.scenario_descriptive_text = ''
        self.scenario_condition = {}
        self.scenario_pict = bytearray()

        self.original_filename = ""

        # debugging
        self.debug = False

    def find_buildings(self, raw_sc2_data):
        """
        Finds all of the buildings in a city file and creates a dict populated with Building objects with the keys being the x, y coordinates of the left corner.
        Building generation algorighm:
            Scan for buildings by looking for their left corner. Why do it this way, which is obviously fragile? Because that's the way the original game did it, and this is attempting to replicate how the original game behaves.
            Once a building is found, look it up in XBLD to determine its size.
            Look for holes (from the magic eraser or other bugs in this building).
            Todo: find building either missing the left corner (rotation) or otherwise "broken" but still supported by the game.
            Buildings are stored as a dictionary, where a tile's xy coordinates are the key. Each tile of a building will point back to the same builiding object. This handles holes in the building.
        Args:
            raw_sc2_data: Raw data for the city.
        Returns:
            Building dictionary.
        """
        # Todo: Check these:
        left_corner = 0b1000
        top_corner = 0b0100
        right_corner = 0b0010
        bottom_corner = 0b0001

        raw_xbld = raw_sc2_data["XBLD"]
        zone_bitmask = raw_sc2_data["XZON"]
        for row in range(self.city_size):
            for col in range(self.city_size):
                # Find left corner.
                zone_mask = zone_bitmask[row][col][: 4]  # Only the the first 4 bits are corner masks.
                if zone_mask & left_corner:
                    if self.debug:
                        print(f"Found Building: {new_building_id} at ({building_x}, {building_y})")
                    building_id = raw_xbld[row][col]
                    building = Building(building_id)
                    self.buildings[(row, col)] = building
                    building_size = buildings.get_size_by_id(building_id)
                    # Now we need to find the rest og the building.
                    for building_x in range(row, row + building_size):
                        for building_y in range(col, col + building_size):
                            new_building_id = raw_xbld[building_x][building_y]
                            if new_building_id == building_id:
                                self.buildings[(row, col)] = building
                                if self.debug:
                                    print(f"Added Building: {new_building_id} at ({building_x}, {building_y})")
                            else:
                                if self.debug:
                                    print(f"Found hole at: ({building_x}, {building_y})")
                                # This should probably be handled, but not yet.



    def create_city_from_file(self, city_path):
        """
        Populates a city object from a .sc2 file.
        Args:
            city_path: Path
        Returns:
            Nothing, used to populate a city object from a file.
        """
        uncompressed_city = self.open_and_uncompress_sc2_file(city_path)
        self.name_city(uncompressed_city)
        self.find_buildings(uncompressed_city)
        self.parse_misc(uncompressed_city["MISC"])


    def name_city(self, uncompressed_data):
        """
        Attempts to name the city based on the filename even if we can't parse a name for the city.
        Truncates to 31 characters and coverts to all caps (as per original SC2k behaviour).
        If the file is old enough and is missing a CNAM section, generates one using the same method.
        Args:
            uncompressed_data: Uncompressed city data.
        """
        try:
            city_name = sc2p.clean_city_name(uncompressed_data['CNAM'])
        except KeyError:
            city_name = ''
            uncompressed_data['CNAM'] = ''
        if len(city_name) == 0:
            city_name = '.'.join(self.original_filename.split('.')[: -1]).upper()
        self.city_name = city_name[:31]

    def open_and_uncompress_sc2_file(self, city_file_path):
        """
        Handles opening and decompression of a city file.
        Args:
            city_file_path: Path to the city file to be opened.
        Returns:
            Uncompressed city data ready for parsing into something more usable.
                This takes the form of a dictionary with the keys being the 4-letter chunk headers from the sc2 IFF file, and the values being the uncompressed raw binary data in bytearray from.
        """
        _, filename = os.path.split(city_file_path)
        self.original_filename = filename
        raw_sc2_file = sc2p.open_file(city_file_path)
        try:
            compressed_data = sc2p.chunk_input_serial(raw_sc2_file, 'sc2')
        except sc2p.SC2Parse:
            raise
        uncompressed_data = sc2p.sc2_uncompress_input(compressed_data, 'sc2')
        return uncompressed_data

    def parse_misc(self, misc_data):
        """
        Parses the MISC section of the .sc2 file and populates the City object with its values.
        See .sc2 file spec docs for more, at:
        Args:
            misc_data (bytes): MISC segment of the raw data from the .sc2 file.
        """
        # This is the offset of the section that's being parsed from MISC.
        parse_order = {
            '0x0000': 'FirstEntry',  # nominally the same in every city.
            '0x0004': 'GameMode',
            '0x0008': 'Compass',  # rotation
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
            '0x0718': 'Valve?|0',  # reverse engineered from the game, may be a typo in original.
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
                          'Military Count', 'Paper List', 'News List', 'Extra'] + list(
            self.simulator_settings.keys()) + list(self.game_settings.keys()) + list(self.inventions.keys())

        # Make sure the dict is sorted because following code requires the sorting.
        sorted(parse_order.keys())

        # Parse misc and generate city attributes.
        for k, v in parse_order.items():
            offset = int(k, 16)
            if v not in handle_special:
                self.city_attributes[v] = misc_data
            elif v == 'Population Graphs':
                length = 240
                self.population_graphs = self.misc_uninterleave_data(self._population_graph_names, offset, length, misc_data)
            elif v == 'Industry Graphs':
                length = 132
                self.industry_graphs = self.misc_uninterleave_data(self._industry_graph_names, offset, length, misc_data)
            elif v == 'Tile Counts':
                for x in range(0, 256):
                    self.building_count.extend([parse_int32(misc_data[offset: offset + 4])])
                    offset += 4
            elif v == 'Bonds':
                # Handled along with the budget.
                continue
            elif v == 'Neighbours':
                neighbour_types = ['Name', 'Population', 'Value', 'Fame']
                # Calculate their offsets. 64 = 4 neighbours at 4 x 4B entries each
                for idx, start_offset in enumerate(range(offset, offset + 64, 16)):
                    # 16 = 4 entries x 4B per entry.
                    neighbour = collections.OrderedDict()
                    for x in range(start_offset, start_offset + 16, 4):
                        type_key = neighbour_types[((x + 8) % 16) // 4]
                        neighbour[type_key] = misc_data
                    self.neighbor_info[idx] = neighbour
            elif v == 'Budget':
                print(k, v)
                #self.budget = Budget(data=misc_data)
            elif v == 'Military Count':
                num_items = 16
                for idx, x in enumerate(range(offset, offset + num_items * 4, 4)):
                    key = "{}|{}".format(v, idx)
                    self.city_attributes[key] = parse_int32(misc_data[x : x + 4])
            elif v == 'Paper List':
                num_items = 6 * 5
                for idx, x in enumerate(range(offset, offset + num_items * 4, 4)):
                    key = "{}|{}".format(v, idx)
                    self.city_attributes[key] = parse_int32(misc_data[x : x + 4])
            elif v == 'News List':
                num_items = 9 * 6
                for idx, x in enumerate(range(offset, offset + num_items * 4, 4)):
                    key = "{}|{}".format(v, idx)
                    self.city_attributes[key] = parse_int32(misc_data[x : x + 4])
            elif v == 'Extra':
                for idx, x in enumerate(range(offset, 4800, 4)):
                    key = "{}|{}".format(v, idx)
                    self.city_attributes[key] = parse_int32(misc_data[x : x + 4])
            elif v in list(self.simulator_settings.keys()):
                self.simulator_settings[v] = parse_int32(misc_data[offset : offset + 4])
            elif v in list(self.game_settings.keys()):
                self.game_settings[v] = parse_int32(misc_data[offset : offset + 4])
            elif v in list(self.inventions.keys()):
                self.inventions[v] = parse_int32(misc_data[offset : offset + 4])
            else:
                # Fallthrough, this should never, ever, be hit.
                print("MISC is missing something!", k, v)

    def misc_uninterleave_data(self, keys, offset, length, misc_data):
        """
        Args:
            keys (): list of keys? representing the data we want to parse.
            offset (int): Offset into MISC where the segment we want to uninterleave starts.
            length (int): Total length of the section.
            misc_data: Data from the MISC section that needs to be uninterlaved
        Returns:
            A dictionary with the key being .
        """
        num_keys = len(keys)
        values = [[] for x in range(num_keys)]
        for idx, val in enumerate(range(offset, offset + length, 4)):
            values[idx % num_keys].extend(misc_data)
        output = {}
        for idx, key_name in enumerate(keys):
            output[key_name] = values[idx]
        return output


class Building:
    def __init__(self, building_id, holes):
        self.building_id = building_id
        self.name = ''  # Todo: Lookup the friendly name from the ID.

    def __str__(self):
        return f"Building{self.name} ({self.building_id})."


class BitFlags:
    """
    Stores the bit flags and implements str() and int().
    """

    def __init__(self, flags):
        _flags = [bool(int(x)) for x in "{0:b}".format(flags).zfill(8)]
        self.powerable = _flags[0]  # Is this a tile that needs power?
        self.powered = _flags[1]  # Is this tile recieving power?
        self.piped = _flags[2]  # Does this tile have pipes underneath it?
        self.watered = _flags[3]  # Is this tile recieving water?
        self.xval = _flags[4]  # Land value of this tile
        self.water = _flags[5]  # Is this tile covered in water?
        self.rotate = _flags[6]  # Should this tile be rotated?
        self.salt = _flags[7]  # Is this tile salt water?

    def __str__(self):
        """
        Returns a binary string representing the bitflags.
        """
        attrs = (self.powerable, self.powered, self.piped, self.watered, self.xval, self.water, self.rotate, self.salt)
        bit_string = ''.join(['1' if x else '0' for x in attrs])
        return bit_string

    def __int__(self):
        """
        Returns the integer corresponding to the flags.
        """
        return int(str(self), 2)


class Budget:
    """
    Class to store budget information.
    """
    def __init__(self, data):
        """
        When creating the budget object
        Args:
            data: raw data that needs to be parsed.
        """
        self.data = data
        self.bonds = []
        offset = 0x0FA0
        self.ordinance_flags = "{0:b}".format(int.from_bytes(self.data[offset: offset + 4], byteorder='big')).zfill(20)

        self.sub_budget_indices = {'Property': {'Residents': 0x077C, 'Commerce': 0x07E8, 'Industry': 0x0854},
                                   'Ordinances': 0x08C0,
                                   'Bonds': 0x0930, 'Police': 0x0998, 'Fire': 0x0A04, 'Health': 0x0A70,
                                   'Education': {'Schools': 0x0ADC, 'Colleges': 0x0B48},
                                   'Transit': {'Road': 0x0BB4, 'Hiway': 0x0C20, 'Bridge': 0x0C8C, 'Rail': 0x0CF8,
                                               'Subway': 0x0D64, 'Tunnel': 0x0DD0}}

        self.sub_budget = copy.deepcopy(self.sub_budget_indices)

        offset = 0x0610
        for val in range(offset, offset + 50 * 4, 4):
            self.bonds.extend([int.from_bytes(self.data[val: val + 4], byteorder='big')])

        for budget_name, budget_values in self.sub_budget_indices.items():
            if type(budget_values) == int:
                split_data = data[budget_values: budget_values + (27 * 4)]
                self.sub_budget[budget_name] = SubBudget(budget_data=split_data, budget_name=budget_name)
            else:
                for sub_budget_name, sub_budget_values in budget_values.items():
                    split_data = data[sub_budget_values: sub_budget_values + (27 * 4)]
                    self.sub_budget[budget_name][sub_budget_name] = SubBudget(budget_data=split_data,
                                                                              budget_name=budget_name)