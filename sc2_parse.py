import sc2_iff_parse as sc2p
import collections
from utils import parse_int32, parse_uint32, parse_uint16, parse_uint8, int_to_bitstring, int_to_bytes, bytes_to_hex, bytes_to_uint, bytes_to_int32s
import os.path
import Data.buildings as buildings
from copy import deepcopy

from struct import unpack


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
        self.labels = {}
        self.microsim_state = {}
        self.graph_data = {}
        self.tilelist = {}
        self.buildings = {}  # Note that this stores *only* buildings.
        self.networks = {}  # Stores roads, rails, powerlines and other things that are above ground networks.
        self.groundcover = {}  # Stores trees, rubble and radioactivity.
        self.things = {}
        self.city_size = 128
        self.graphs = {k: None for k in self._graph_window_graphs}

        # Stuff from Misc
        self.city_attributes = {}
        self.budget = None
        self.neighbor_info = {}
        self.building_count = {}
        self.simulator_settings = {}
        self.inventions = {}
        self.population_graphs = {}
        self.industry_graphs = {}
        self.simulator_settings = {x: None for x in self._simulator_setting_names}
        self.game_settings = {x: None for x in self._game_setting_names}
        self.inventions = {x: None for x in self._invention_names}
        # Minimaps
        self.traffic = Minimap("traffic", 64)
        self.pollution = Minimap("pollution", 64)
        self.value = Minimap("value", 64)
        self.crime = Minimap("crime", 64)
        self.police = Minimap("police", 32)
        self.fire = Minimap("fire", 32)
        self.density = Minimap("density", 32)
        self.growth = Minimap("growth", 32)

        # Optional Scenario stuff
        self.is_scenario = False
        self.scenario_text = ''
        self.scenario_descriptive_text = ''
        self.scenario_condition = {}
        self.scenario_pict = []

        self.original_filename = ""

        # debugging
        self.debug = False

    def create_minimaps(self, raw_sc2_data):
        """
        Creates the 8 minimaps.
        Args:
            raw_sc2_data (bytes): Uncompressed .sc2 file.
        """
        # Minimaps that map 4 tiles to 1.
        map_size = self.city_size // 2
        for x in range(map_size):
            for y in range(map_size):
                tile_idx = x * map_size + y
                tile_key = (x, y)
                xtrf = raw_sc2_data["XTRF"][tile_idx: tile_idx + 1]
                xplt = raw_sc2_data["XPLT"][tile_idx: tile_idx + 1]
                xval = raw_sc2_data["XVAL"][tile_idx: tile_idx + 1]
                xcrm = raw_sc2_data["XCRM"][tile_idx: tile_idx + 1]
                self.traffic[tile_key] = parse_uint8(xtrf)
                self.pollution[tile_key] = parse_uint8(xplt)
                self.value[tile_key] = parse_uint8(xval)
                self.crime[tile_key] = parse_uint8(xcrm)
                if self.debug:
                    print(f"{tile_key}: traffic: {parse_uint8(xtrf)}, pollution: {parse_uint8(xplt)}, land value: {parse_uint8(xval)}, crime: {parse_uint8(xcrm)}\n")
        # Minimaps that map 16 tiles to 1.
        map_size_small = self.city_size // 4
        for x in range(map_size_small):
            for y in range(map_size_small):
                tile_idx = x * map_size_small + y
                tile_key = (x, y)
                xplc = raw_sc2_data["XPLC"][tile_idx: tile_idx + 1]
                xfir = raw_sc2_data["XFIR"][tile_idx: tile_idx + 1]
                xpop = raw_sc2_data["XPOP"][tile_idx: tile_idx + 1]
                xrog = raw_sc2_data["XROG"][tile_idx: tile_idx + 1]
                self.police[tile_key] = parse_uint8(xplc)
                self.fire[tile_key] = parse_uint8(xfir)
                self.density[tile_key] = parse_uint8(xpop)
                self.growth[tile_key] = parse_uint8(xrog)
                if self.debug:
                    print(f"{tile_key}: police: {parse_uint8(xplc)}, fire: {parse_uint8(xfir)}, densitye: {parse_uint8(xpop)}, growth: {parse_uint8(xrog)}\n")

    def create_tilelist(self, raw_sc2_data):
        """
        Stores information about a tile.
        Args:
            raw_sc2_data (bytes): Uncompressed .sc2 file.
        """
        for row in range(self.city_size):
            for col in range(self.city_size):
                tile = Tile(self.traffic, self.pollution, self.value, self.crime, self.police, self.fire,  self.density, self.growth, self.labels)
                tile_idx = row * self.city_size + col
                tile_coords = (row, col)
                tile.coordinates = tile_coords
                if self.debug:
                    print(f"index: {tile_idx} at {tile_coords}")
                # First start with parsing the terrain related features.
                altm = raw_sc2_data["ALTM"][tile_idx * 2 : tile_idx * 2 + 2]
                xter = raw_sc2_data["XTER"][tile_idx : tile_idx + 1]
                altm_bits = int_to_bitstring(parse_uint16(altm), 16)
                tile.is_water = bool(int(altm_bits[7 : 8], 2))
                tile.altitude_unknown = int(altm_bits[8 : 10], 2)
                tile.altitude = int(altm_bits[11 : ], 2)
                tile.terrain = parse_uint8(xter)
                if self.debug:
                    print(f"altm: {altm_bits}, xter: {tile.terrain}")
                tile.altidue_tunnel = int(altm_bits[0 : 7], 2)
                # Next parse city stuff.
                # skip self.building for now, it's handled specially.
                xzon = raw_sc2_data["XZON"][tile_idx : tile_idx + 1]
                xzon_bits = int_to_bitstring(parse_uint8(xzon), 8)
                tile.zone_corners = xzon_bits[0 : 4]
                tile.zone = int(xzon_bits[4 : ], 2)
                xund = raw_sc2_data["XUND"][tile_idx : tile_idx + 1]
                tile.underground = parse_uint8(xund)
                if self.debug:
                    print(f"zone: {tile.zone}, corners: {tile.zone_corners}, underground: {tile.underground}")
                # text/signs
                xtxt = raw_sc2_data["XTXT"][tile_idx : tile_idx + 1]
                tile.text_pointer = parse_uint8(xtxt)
                # bit flags
                xbit = raw_sc2_data["XBIT"][tile_idx : tile_idx + 1]
                tile.bit_flags = BitFlags(parse_uint8(xbit))
                if self.debug:
                    print(f"text pointer: {tile.text_pointer}, bit flags: {tile.bit_flags}")
                # Add the new tile to the tilelist
                self.tilelist[(row, col)] = tile

    def parse_labels(self, xlab_segment):
        """
        Parses the label data.
        Todo: Make handling of "special" labels easier.
        Args:
            xlab_segment (bytes): XLAB sgement of the raw .sc2 file.
        """
        for x in range(0, len(xlab_segment), 25):
            label_id = x // 25
            raw_label = xlab_segment[x : x + 25]
            label_len = parse_uint8(raw_label[0 : 1])
            label = raw_label[1 : label_len + 1].decode('ascii', 'replace')

            self.labels[label_id] = label
            if self.debug:
                print(f"Label: {label_id}: '{label}'")

    def parse_microsim(self, xmic_segment):
        """
        Parses the label data.
        Note that this is incomplete and contains the raw bytes presently.
        Args:
            xmic_segment (bytes): XMIC sgement of the raw .sc2 file.
        """
        for x in range(0, len(xmic_segment), 8):
            microsim_id = x // 8
            microsim = xmic_segment[x : x + 8]
            self.microsim_state[microsim_id] = microsim
            if self.debug:
                print(f"Raw Microsim: {microsim_id}: {bytes_to_hex(microsim)}")

    def parse_things(self, xthg_segments):
        """
        Parses the XTHG segment.
        Note: incompolete as XTHG segment spec not fully known.
        Args:
            xthg_segments (bytes): Raw bytes representing the segment.
        """
        for idx in range(0, len(xthg_segments), 12):
            thing_data = xthg_segments[idx : idx + 12]
            thing_index = idx // 12
            thing = Thing()
            thing.parse_thing(thing_data)
            if self.debug:
                print(f"Index: {thing_index}, {thing}")
            self.things[thing_index] = thing

    def parse_graphs(self, xgrp_segment):
        """
        Parses the various graphs.
        Args:
            xgrp_segment (bytes): Raw graph data to parse
        """
        segment_len = 52 * 4
        for idx, graph_name in enumerate(self._graph_window_graphs):
            graph = Graph()
            graph_start = idx * segment_len
            graph.parse_graph(xgrp_segment[graph_start : graph_start + segment_len])
            self.graphs[graph_name] = graph
            if self.debug:
                print(f"Graph: {graph_name}\n{graph}")

    def parse_scenario(self, raw_city_data):
        """
        Parses the scenario information.
        Args:
            raw_city_data (bytes): Raw data to parse scenario information out of.
        """
        self.is_scenario = True

        raw_text = raw_city_data["TEXT"]
        raw_scenario = raw_city_data["SCEN"]
        picture = raw_city_data["PICT"]

        for entry in raw_text:
            string_id = entry[: 4]
            raw_string = entry[4 :].decode('ASCII').replace('\r', '\n')
            if string_id == b'\x80\x00\x00\x00':
                self.scenario_text = raw_string
            elif string_id == b'\x81\x00\x00\x00':
                self.scenario_descriptive_text = raw_string
            else:
                print(f"Found unknown TEXT block in input file.\nid: {string_id}, contents: \"{raw_string}\"")
        if self.debug:
            print(f"Scenario:\nShort text: {self.scenario_text}\nDescriptive Text:{self.scenario_descriptive_text}")

        conditions = {}
        offset = 4
        contents = collections.OrderedDict((
            ("disaster_type", 2),
            ("distater_x_location", 1),
            ("disaster_y_location", 1),
            ("time_limit_months", 2),
            ("city_size_goal", 4),
            ("residential_goal", 4),
            ("commercial_goal", 4),
            ("industrial_goal", 4),
            ("cash_flow_goal-bonds", 4),
            ("land_value_goal", 4),
            ("pollution_limit", 4),
            ("traffic_limit", 4),
            ("crime_limit", 4),
            ("build_item_one", 1),
            ("build_item_two", 1),
            ("item_one_tiles", 2),
            ("item_two_tiles", 2),))
        for k, v in contents.items():
            conditions[k] = bytes_to_uint(raw_scenario[offset : offset + v])
            offset += v
            if self.debug:
                print(f"Conditions: {conditions}")
            self.scenario_condition = conditions

        header = picture[0 : 4]
        if header != bytearray(b'\x80\x00\x00\x00'):
            print("Scenario PICT parsing failed.")  # todo: exception?
        # Why is the endianness different here? It just is.
        row_length = unpack('<H', picture[4 : 6])[0]  # x dimension of image.
        row_count = unpack('<H', picture[6 : 8])[0]  # y dimension of image.
        image_data = []
        picture_data = picture[8 : ]
        if self.debug:
            print(f"Scenario PICT, {row_length}x{row_count} pixels:")
        for row_idx in range(0, row_count):
            row_start = row_idx * (row_length + 1)
            row = [x for x in picture_data[row_start : row_start + row_length + 1]]
            if row[-1] != 255:
                row = [0] * row_length
            else:
                row = row[ : -1]
            image_data.append(row)
        if self.debug:
            for idx, r in enumerate(image_data):
                print(f"{idx}:\n{r}")
        self.scenario_pict = image_data

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
        """
        # Todo: Check this:
        left_corner = 0b1000

        groundcover_ids = list(range(0x01, 0x0D + 1))
        network_ids = list(range(0x0E, 0x79 + 1))

        raw_xbld = raw_sc2_data["XBLD"]
        for row in range(self.city_size):
            for col in range(self.city_size):
                # Find left corner.
                zone_mask = self.tilelist[(row, col)].zone_corners
                if self.debug:
                    print(f"Checking building at: ({row}, {col})")
                if int(zone_mask, 2) & left_corner:
                    tile_idx = row * self.city_size + col
                    building_id = raw_xbld[tile_idx]
                    new_building = Building(building_id, (row, col))
                    self.buildings[(row, col)] = new_building
                    self.tilelist[(row, col)].building = new_building
                    building_size = buildings.get_size(building_id)
                    if self.debug:
                        print(f"Found Building: {building_id} with size: {building_size} at ({row}, {col})")

                    # Now we need to find the rest og the building.
                    if building_size == 1:
                        continue
                    # The clamping to 127 is to deal with certain industrial 3x3 buildings that glitch out on the edge of the map.
                    for building_x in range(row, min(row + building_size + 1, 127)):
                        for building_y in range(col, col - building_size, -1):
                            next_tile_idx = building_x * self.city_size + building_y
                            new_building_id = raw_xbld[next_tile_idx]
                            if new_building_id == building_id:
                                self.tilelist[(building_x, building_y)].building = new_building
                                if self.debug:
                                    print(f"Added Building: {new_building_id} at ({building_x}, {building_y})")
                            else:
                                if self.debug:
                                    print(f"Found hole at: ({building_x}, {building_y})")
                                    # This should probably be handled, but not yet.
                else:
                    # Why are groundcover and networks treated differently?
                    # Because it seems (seemed?) to add flexibility.
                    tile_idx = row * self.city_size + col
                    building_id = raw_xbld[tile_idx]
                    if building_id in groundcover_ids:
                        new_building = Building(building_id, (row, col))
                        self.groundcover[(row, col)] = new_building
                        self.tilelist[(row, col)].building = new_building
                        if self.debug:
                            print(f"Found groundcover: {building_id} at ({row}, {col})")
                    elif building_id in network_ids:
                        new_building = Building(building_id, (row, col))
                        self.networks[(row, col)] = new_building
                        self.tilelist[(row, col)].building = new_building
                        if self.debug:
                            print(f"Found network: {building_id} at ({row}, {col})")
                    else:
                        if self.debug:
                            print(f"Tile parsing fallthrough at ({building_x}, {building_y}) with id: {new_building_id}")
                        pass



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
        self.create_minimaps(uncompressed_city)
        self.create_tilelist(uncompressed_city)
        self.find_buildings(uncompressed_city)
        self.parse_misc(uncompressed_city["MISC"])
        self.parse_labels(uncompressed_city["XLAB"])
        self.parse_microsim(uncompressed_city["XMIC"])
        self.parse_things(uncompressed_city["XTHG"])
        self.parse_graphs(uncompressed_city["XGRP"])

        # Check for scenario.
        if all(x in uncompressed_city.keys() for x in ("TEXT", "SCEN", "PICT")):
            self.parse_scenario(uncompressed_city)

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
        #sorted(parse_order.keys())

        # Parse misc and generate city attributes.
        for k, v in parse_order.items():
            offset = int(k, 16)
            if v not in handle_special:
                self.city_attributes[v] = parse_uint32(misc_data[offset : offset + 4])
            elif v == 'Population Graphs':
                length = 240
                self.population_graphs = self.misc_uninterleave_data(self._population_graph_names, offset, length, misc_data)
            elif v == 'Industry Graphs':
                length = 132
                self.industry_graphs = self.misc_uninterleave_data(self._industry_graph_names, offset, length, misc_data)
            elif v == 'Tile Counts':
                for x in range(0, 256):
                    self.building_count[x] = parse_int32(misc_data[offset: offset + 4])
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
                self.budget = Budget()
                self.budget.parse_budget(misc_data)
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
    def __init__(self, building_id, coords):
        self.building_id = building_id
        self.name = buildings.get_name(building_id)
        self.tile_coords = coords

    def __str__(self):
        tile_x = self.tile_coords[0]
        tile_y = self.tile_coords[1]
        return f"Building: {self.name} ({self.building_id}) at ({tile_x}, {tile_y})."


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

    def to_int(self):
        """
        Converts the bitflags to an int.
        Returns:
            An integer representation of the flags.
        """
        res = [self.powerable, self.powered, self.piped, self.watered, self.xval, self.water, self.rotate, self.salt]
        res = ''.join([str(int(x == True)) for x in res])
        return int(res, 2)

    def to_byte(self):
        """
        Converts this bitflags to a bytes.
        Returns:
            A single, big endian byte representation of the bitflags.
        """
        return int_to_bytes(self.to_int(), 1)


class Budget:
    """
    Class to store budget information.
    """
    _blank_budget = {
        "current_count": 0,
        "current_funding": 0,
        "unknown": 0,
        "jan_count": 0,
        "jan_funding": 0,
        'feb_funding': 0,
        'feb_count': 0,
        'mar_funding': 0,
        'mar_count': 0,
        'apr_funding': 0,
        'apr_count': 0,
        'may_funding': 0,
        'may_count': 0,
        'jun_funding': 0,
        'jun_count': 0,
        'jul_funding': 0,
        'jul_count': 0,
        'aug_funding': 0,
        'aug_count': 0,
        'sep_funding': 0,
        'sep_count': 0,
        'oct_funding': 0,
        'oct_count': 0,
        'nov_funding': 0,
        'nov_count': 0,
        'dec_funding': 0,
        'dec_count': 0,
    }
    _sub_budget_indices = {'Residential': 0x077C, 'Commercial': 0x07E8, 'Industrial': 0x0854,
                           'Bonds': 0x0930, 'Police': 0x0998, 'Fire': 0x0A04, 'Health': 0x0A70,
                           'Schools': 0x0ADC, 'Colleges': 0x0B48,
                           'Road': 0x0BB4, 'Hiway': 0x0C20, 'Bridge': 0x0C8C, 'Rail': 0x0CF8, 'Subway': 0x0D64,
                           'Tunnel': 0x0DD0}

    def __init__(self):
        self.budget_items = deepcopy(self._sub_budget_indices)
        self.bonds = [0] * 50
        self.ordinance_flags = '0' * 20

    def parse_budget(self, raw_misc_data):
        """
        Parses the budget data segment from MISC into budget data.
        Args:
            raw_misc_data (bytes): Raw segment from Misc
        """
        # Ordinances
        ordinance_raw = raw_misc_data[0x0FA0 : 0x0FA0 + 4]
        self.ordinance_flags = int_to_bitstring(parse_uint32(ordinance_raw))

        # bonds
        start_offset = 0x0610
        bonds_len = 50 * 4
        self.bonds = bytes_to_int32s(raw_misc_data[start_offset : start_offset + bonds_len])

        # various sub-budgets
        sub_len = 27 * 4
        for name, start_offset in self._sub_budget_indices.items():
            chunk = raw_misc_data[start_offset : start_offset + sub_len]
            sub_budget = deepcopy(self._blank_budget)
            chunk_data = bytes_to_int32s(chunk)
            for idx, k in enumerate(self._blank_budget):
                sub_budget[k] = chunk_data[idx]
            self.budget_items[name] = sub_budget




class Tile(City):
    """
    Stores all the information related to a tile.
    """
    def __init__(self, traffic, pollution, value, crime, police, fire, density, growth, label):
        self.coordinates = (0, 0)
        # Altitude map related values.
        self.altidue_tunnel = 0
        self.is_water = 0
        self.altitude_unknown = 0
        self.altitude = 0
        # Terrain
        self.terrain = 0
        # City stuff
        self.building = None
        self.zone_corners = 0
        self.zone = 0
        self.underground = 0
        self._label = label
        # text/signs
        self.text_pointer = None
        # bit flags
        self.bit_flags = None
        # minimaps/simulation stuff
        self._traffic_minimap = traffic
        self._pollution_minimap = pollution
        self._value_minimap = value
        self._crime_minimap = crime
        self._police_minimap = police
        self._fire_minimap = fire
        self._density_minimap = density
        self._growth_minimap = growth

    @property
    def traffic(self):
        return self._traffic_minimap.get_scaled(self.coordinates)

    @traffic.setter
    def traffic(self, val):
        self._traffic_minimap.set_scaled(self.coordinates, val)

    @property
    def pollution(self):
        return self._pollution_minimap.get_scaled(self.coordinates)

    @pollution.setter
    def pollution(self, val):
        self._pollution_minimap.set_scaled(self.coordinates, val)

    @property
    def value(self):
        return self._value_minimap.get_scaled(self.coordinates)

    @value.setter
    def value(self, val):
        self._value_minimap.set_scaled(self.coordinates, val)

    @property
    def crime(self):
        return self._crime_minimap.get_scaled(self.coordinates)

    @crime.setter
    def crime(self, val):
        self._crime_minimap.set_scaled(self.coordinates, val)

    @property
    def police(self):
        return self._police_minimap.get_scaled(self.coordinates)

    @police.setter
    def police(self, val):
        self._police_minimap.set_scaled(self.coordinates, val)

    @property
    def fire(self):
        return self._fire_minimap.get_scaled(self.coordinates)

    @fire.setter
    def fire(self, val):
        self._fire_minimap.set_scaled(self.coordinates, val)

    @property
    def density(self):
        return self._density_minimap.get_scaled(self.coordinates)

    @density.setter
    def density(self, val):
        self._density_minimap.set_scaled(self.coordinates, val)

    @property
    def growth(self):
        return self._growth_minimap.get_scaled(self.coordinates)

    @growth.setter
    def growth(self, val):
        self._growth_minimap.set_scaled(self.coordinates, val)

    @property
    def text(self):
        return self._label[self.text_pointer]

    @text.setter
    def text(self, val):
        self._label[self.text_pointer] = val

    def __str__(self):
        s = f"Tile at {self.coordinates}\n"
        s += f"Altitude:\n\ttunnel: {self.altidue_tunnel}, water: {self.altitude_water}, unknown: {self.altitude_unknown}, altitude: {self.altitude}\n"
        terr = int_to_bitstring(self.terrain)
        s += f"Terrain: {terr}\n"
        # City stuff
        try:
            b_id = self.building.building_id
        except:
            b_id = "None"
        s += f"Buildings:\n\tid: {b_id}, corners {self.zone_corners}, zone: {self.zone}, underground: {self.underground}\n"
        # text/signs
        sign_text = ''
        if self.text_pointer:
            sign_text = f", Sign: \"{self.text}\""
        s += f"Text pointer: {self.text_pointer}{sign_text}\n"
        # bit flags
        s += f"Flags: {self.bit_flags}\n"
        # minimaps/simulation stuff
        s += f"Minimap:\n\tTraffic: {self.traffic}, pollution: {self.pollution}, value: {self.value}, crime: {self.crime}, police: {self.police}, fire: {self.fire}, density: {self.density}, growth: {self.growth}."
        return s


class Thing:
    """
    Class to represent a thing stored in the XTHG segment.
    """
    def __init__(self):
        self.thing_id = 0
        self.rotation_1 = 0
        self.rotation_2 = 0
        self.x = 0
        self.y = 0
        self.data = [0] * 7

    def parse_thing(self, raw_thing):
        """
        Parses raw bytes into a thing.
        Args:
            raw_thing (bytes):  12 bytes representing the thing.
        """
        # Why the index? Because python appears to automatically convert this to an int.
        self.thing_id = raw_thing[0]
        self.rotation_1 = raw_thing[1]
        self.rotation_2 = raw_thing[2]
        self.x = raw_thing[3]
        self.y = raw_thing[4]
        self.data = [raw_thing[x] for x in range(4, 12)]

    def __str__(self):
        return f"Thing with ID: { self.thing_id} at ({self.x}, {self.y}), rotations: {self.rotation_1}, {self.rotation_2}, data: {self.data}"

class Graph:
    """
    Stores the data for a graph.
    """
    def __init__(self):
        self.one_year = [0] * 12
        self.ten_years = [0] * 20
        self.hundred_years = [0] * 20

    def parse_graph(self, raw_graphs):
        start = 0
        self.one_year = [parse_int32(raw_graphs[x : x + 4]) for x in range(start, start + 12 * 4, 4)]
        start += 12 * 4
        self.ten_years = [parse_int32(raw_graphs[x : x + 4]) for x in range(start, start + 20 * 4, 4)]
        start += 20 * 4
        self.hundred_years = [parse_int32(raw_graphs[x : x + 4]) for x in range(start, start + 20 * 4, 4)]

    def __str__(self):
        s = f"Year:\n\t{[x for x in self.one_year]}.\n"
        s += f"10 Years:\n\t{[x for x in self.ten_years]}.\n"
        s += f"100 Years:\n\t{[x for x in self.hundred_years]}.\n"
        return s


class Minimap:
    """
    Couldn't think of a better name, but this stores minimap info/simulation variables stores in:
    XTRF, XPLT, XVAL, XCRM, XPLC, XFIR, XPOP, XROG.
    """
    _x64 = ["XTRF", "XPLT", "XVAL", "XCRM"]
    _x32 = ["XPLC", "XFIR", "XPOP", "XROG"]

    def __init__(self, name='', size=0):
        self.name = name
        self.data = {}
        self.size = size

    def convert_xy(self, key):
        x, y = key
        d = 4
        if self.size == 64:
            d = 2
        x //= d
        y //= d
        return (x, y)

    def get_scaled(self, key):
        new_key = self.convert_xy(key)
        return self.data[new_key]

    def set_scaled(self, key, item):
        new_key = self.convert_xy(key)
        self.data[new_key] = item

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __str__(self):
        s = f"{self.name}:\n "
        for x in range(self.size):
            for y in range(self.size):
                s += f"{y} "
            s += '\n'
        return s
