"""
The purpose of this file is to store data reverse engineered from the game about buildings.
This will likely get split out into a JSON or similar file at some point, but for now, it's all in this file.
"""


"""
Stores basic information about a tile.

If an attribute is not specified, it is assumed to not apply to the tile, or be False.
Tile attributes:
    name: Nice name for the tile.
    size: How big is the tile? Since all tiles are square, this is the dimension of the edge.
    corners: Will this tile have corners set in XZON?
    water: Does this tile need water? If so, it'll have pipes underneath it.
    power: Does this tile consume power.
    zone: What zone is this tile?
        Possible Values are: residential, commercial, industrial, military, airport, seaport & special.
        Note that this doesn't differentiate between density. This might change later, but only 1x1 buildings can form in low-density zones.
    construction: Whether or not this tile is considered constuction. Handled differently if so.
    abandoned: Whether or not this tils represents an abandoned building. Handled differently if it is.
    power_generated: Does this tile generate power? Amount of power generated will be stored elsewhere to account for power plants that generate variable amounts of power. See Wind and Solar.
    power_reported: Nominally, how much does this building supposedly produce (in MW). As reported in game.
    water_produced: Does this building produce water? Amount stored in separate data structure.
    cost: How much does it cost to plop this tile?
    maintenance: How much does this building cost /year at 100% funding?
    underground: What underground tile id should this tile have?
        Note that if water = True, this is assumed to be the normal small pipes. Otherwise, use the special tile.
    microsim: What microsim applies to this tile (if any?)
        Possible Values: city_hall, hospital, police, fire, museum, park, school, stadium, prison, college, zoo, statue, library, bus, rail, wind, hydro, marina, subway, plymouth, forest, darco, launch, dome, mansion.

"""
tile_data = {
    # Ground Cover
    0x00: {
        "name": "Clear Ground",
        "size": 1,
    },
    0x01: {
        "name": "Rubble 1",
        "size": 1,
    },
    0x02: {
        "name": "Rubble 2",
        "size": 1,
    },
    0x03: {
        "name": "Rubble 3",
        "size": 1,
    },
    0x04: {
        "name": "Rubble 4",
        "size": 1,
    },
    0x05: {
        "name": "Radioactive Waste",
        "size": 1,
    },
    0x06: {
        "name": "Tree",
        "size": 1,
    },
    0x07: {
        "name": "Couple O Trees",
        "size": 1,
    },
    0x08: {
        "name": "More Trees",
        "size": 1,
    },
    0x09: {
        "name": "Morer Trees",
        "size": 1,
    },
    0x0A: {
        "name": "Even More Trees",
        "size": 1,
    },
    0x0B: {
        "name": "Tons O Trees",
        "size": 1,
    },
    0x0C: {
        "name": "Veritable Jungle",
        "size": 1,
    },
    0x0D: {
        "name": "Small Park",
        "size": 1,
        "corners": True,
        "water": True,
        "cost": 20,
    },
    # Power Lines
    0x0E: {
        "name": "Power Line: Left-Right",
        "size": 1,
    },
    0x0F: {
        "name": "Power Line: Top-Bottom",
        "size": 1,
    },
    0x10: {
        "name": "Power Line: HighTop-Bottom",
        "size": 1,
    },
    0x11: {
        "name": "Power Line: Left-HighRight",
        "size": 1,
    },
    0x12: {
        "name": "Power Line: Top-HighBottom",
        "size": 1,
    },
    0x13: {
        "name": "Power Line: HighLeft-Right",
        "size": 1,
    },
    0x14: {
        "name": "Power Line: Bottom-Right",
        "size": 1,
    },
    0x15: {
        "name": "Power Line: Bottom-Left",
        "size": 1,
    },
    0x16: {
        "name": "Power Line: Top-Left",
        "size": 1,
    },
    0x17: {
        "name": "Power Line: Top-Right",
        "size": 1,
    },
    0x18: {
        "name": "Power Line: Right-Top-Left",
        "size": 1,
    },
    0x19: {
        "name": "Power Line: Right-Bottom-Left",
        "size": 1,
    },
    0x1A: {
        "name": "Power Line: Top-Left-Bottom",
        "size": 1,
    },
    0x1B: {
        "name": "Power Line: Left-Top-Bottom",
        "size": 1,
    },
    0x1C: {
        "name": "Power Line: Left-Top-Bottom-Right",
        "size": 1,
    },
    # Roads
    0x1D: {
        "name": "Road: Left-Right",
        "size": 1,
    },
    0x1E: {
        "name": "Road: Top-Bottom",
        "size": 1,
    },
    0x1F: {
        "name": "Road: HighTop-Bottom",
        "size": 1,
    },
    0x20: {
        "name": "Road: Left-HighRight",
        "size": 1,
    },
    0x21: {
        "name": "Road: Top-HighBottom",
        "size": 1,
    },
    0x22: {
        "name": "Road: HighLeft-Right",
        "size": 1,
    },
    0x23: {
        "name": "Road: Bottom-Right",
        "size": 1,
    },
    0x24: {
        "name": "Road: Bottom-Left",
        "size": 1,
    },
    0x25: {
        "name": "Road: Top-Left",
        "size": 1,
    },
    0x26: {
        "name": "Road: Top-Right",
        "size": 1,
    },
    0x27: {
        "name": "Road: Right-Top-Left",
        "size": 1,
    },
    0x28: {
        "name": "Road: Right-Bottom-Left",
        "size": 1,
    },
    0x29: {
        "name": "Road: Top-Left-Bottom",
        "size": 1,
    },
    0x2A: {
        "name": "Road: Left-Top-Bottom",
        "size": 1,
    },
    0x2B: {
        "name": "Road: Left-Top-Bottom-Right",
        "size": 1,
    },
    # Rail
    0x2C: {
        "name": "Rail: Left-Right",
        "size": 1,
    },
    0x2D: {
        "name": "Rail: Top-Bottom",
        "size": 1,
    },
    0x2E: {
        "name": "Rail: HighTop-Bottom",
        "size": 1,
    },
    0x2F: {
        "name": "Rail: Left-HighRight",
        "size": 1,
    },
    0x30: {
        "name": "Rail: Top-HighBottom",
        "size": 1,
    },
    0x31: {
        "name": "Rail: HighLeft-Right",
        "size": 1,
    },
    0x32: {
        "name": "Rail: Bottom-Right",
        "size": 1,
    },
    0x33: {
        "name": "Rail: Bottom-Left",
        "size": 1,
    },
    0x34: {
        "name": "Rail: Top-Left",
        "size": 1,
    },
    0x35: {
        "name": "Rail: Top-Right",
        "size": 1,
    },
    0x36: {
        "name": "Rail: Right-Top-Left",
        "size": 1,
    },
    0x37: {
        "name": "Rail: Right-Bottom-Left",
        "size": 1,
    },
    0x38: {
        "name": "Rail: Top-Left-Bottom",
        "size": 1,
    },
    0x39: {
        "name": "Rail: Left-Top-Bottom",
        "size": 1,
    },
    0x3A: {
        "name": "Rail: Left-Top-Bottom-Right",
        "size": 1,
    },
    0x3B: {
        "name": "Rail: HighTop-Bottom",
        "size": 1,
    },
    0x3C: {
        "name": "Rail: Left-HighRight",
        "size": 1,
    },
    0x3D: {
        "name": "Rail: Top-HighBottom",
        "size": 1,
    },
    0x3E: {
        "name": "Rail: HighLeft-Right",
        "size": 1,
    },
    # Tunnels
    0x3F: {
        "name": "Tunnel: Top",
        "size": 1,
    },
    0x40: {
        "name": "Tunnel: Right",
        "size": 1,
    },
    0x41: {
        "name": "Tunnel: Bottom",
        "size": 1,
    },
    0x42: {
        "name": "Tunnel: Left",
        "size": 1,
    },
    # Crossovers
    0x43: {
        "name": "Power:Top-Bottom, Road:Left-Right",
        "size": 1,
    },
    0x44: {
        "name": "Power:Left-Right, Road:Top-Bottom",
        "size": 1,
    },
    0x45: {
        "name": "Road:Left-Right, Rail:Top-Bottom",
        "size": 1,
    },
    0x46: {
        "name": "Road:Top-Bottom, Rail:Left-Right",
        "size": 1,
    },
    0x47: {
        "name": "Rail:Left-Right, Power:Top-Bottom",
        "size": 1,
    },
    0x48: {
        "name": "Rail:Top-Bottom, Power:Left-Right",
        "size": 1,
    },
    # Highways
    0x49: {
        "name": "Highway: Left-Right",
        "size": 1,
    },
    0x4A: {
        "name": "Highway: Top-Bottom",
        "size": 1,
    },
    # Highway Crossovers
    0x4B: {
        "name": "Highway:Left-Right, Road:Top-Bottom",
        "size": 1,
    },
    0x4C: {
        "name": " Highway:Top-Bottom, Road:Left-Right",
        "size": 1,
    },
    0x4D: {
        "name": "Highway:Left-Right, Rail:Top-Bottom",
        "size": 1,
    },
    0x4E: {
        "name": "Highway:Top-Bottom, Rail:Left-Right",
        "size": 1,
    },
    0x4F: {
        "name": "Highway:Top-Bottom, Power:Left-Right",
        "size": 1,
    },
    0x50: {
        "name": "Highway:Left-Right, Power:Top-Bottom",
        "size": 1,
    },
    # Bridges
    0x51: {
        "name": "Suspension Bridge: Start:Bottom",
        "size": 1,
    },
    0x52: {
        "name": "Suspension Bridge: Middle:Bottom",
        "size": 1,
    },
    0x53: {
        "name": "Suspension Bridge: Center",
        "size": 1,
    },
    0x54: {
        "name": "Suspension Bridge: Middle:Top",
        "size": 1,
    },
    0x55: {
        "name": "Suspension Bridge: Start:Top",
        "size": 1,
    },
    0x56: {
        "name": "Raising Bridge: Tower",
        "size": 1,
    },
    0x57: {
        "name": "Bridge: Pylon",
        "size": 1,
    },
    0x58: {
        "name": "Bridge: Deck",
        "size": 1,
    },
    0x59: {
        "name": "Raising Bridge: Deck:Raised",
        "size": 1,
    },
    0x5A: {
        "name": "Rail Bridge: Pylon",
        "size": 1,
    },
    0x5B: {
        "name": "Rail Bridge: Deck",
        "size": 1,
    },
    0x5C: {
        "name": "Raised Power Lines",
        "size": 1,
    },
    # Onramps
    0x5D: {
        "name": "Onramp: Highway:Top-Road:Left",
        "size": 1,
        "cost": 25,
    },
    0x5E: {
        "name": "Onramp: Highway:Top-Road:Right",
        "size": 1,
        "cost": 25,
    },
    0x5F: {
        "name": "Onramp: Highway:Bottom-Road:Left",
        "size": 1,
        "cost": 25,
    },
    0x60: {
        "name": "Onramp: Highway:Bottom-Road:Right",
        "size": 1,
        "cost": 25,
    },
    # Highways
    0x61: {
        "name": "Highway: HighTop-Bottom",
        "size": 2,
    },
    0x62: {
        "name": "Highway: Left-HighRight",
        "size": 2,
    },
    0x63: {
        "name": "Highway: Top-HighBottom",
        "size": 2,
    },
    0x64: {
        "name": "Highway: HighLeft-Right",
        "size": 2,
    },
    0x65: {
        "name": "Highway: Bottom-Right",
        "size": 2,
    },
    0x66: {
        "name": "Highway: Bottom-Left",
        "size": 2,
    },
    0x67: {
        "name": "Highway: Top-Left",
        "size": 2,
    },
    0x68: {
        "name": "Highway: Top-Right",
        "size": 2,
    },
    0x69: {
        "name": "Highway: Left-Top-Bottom-Right",
        "size": 2,
    },
    # Highway Reinforced Bridge
    0x6A: {
        "name": "Highway Reinforced Bridge Pylon",
        "size": 2,
    },
    0x6B: {
        "name": "Highway Reinforced Bridge",
        "size": 2,
    },
    # Sub -> Rail
    0x6C: {
        "name": "Sub-Rail: Top",
        "size": 1,
        "underground": 0x23,
        "cost": 250,
    },
    0x6D: {
        "name": "Sub-Rail: Right",
        "size": 1,
        "underground": 0x23,
        "cost": 250,
    },
    0x6E: {
        "name": "Sub-Rail: Bottom",
        "size": 1,
        "underground": 0x23,
        "cost": 250,
    },
    0x6F: {
        "name": "Sub-Rail: Left",
        "size": 1,
        "underground": 0x23,
        "cost": 250,
    },
    # Residential 1x1
    0x70: {
        "name": "Lower Class Homes 1",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x71: {
        "name": "Lower Class Homes 2",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x72: {
        "name": "Lower Class Homes 3",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x73: {
        "name": "Lower Class Homes 4",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x74: {
        "name": "Middle Class Homes 1",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x75: {
        "name": "Middle Class Homes 2",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x76: {
        "name": "Middle Class Homes 3",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x77: {
        "name": "Middle Class Homes 4",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x78: {
        "name": "Upper Class Homes 1",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x79: {
        "name": "Upper Class Homes 2",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x7A: {
        "name": "Upper Class Homes 3",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x7B: {
        "name": "Upper Class Homes 4",
        "size": 1,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    # Commercial 1x1
    0x7C: {
        "name": "Gas Station 1",
        "size": 1,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x7D: {
        "name": "Bed & Breakfast Inn",
        "size": 1,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x7E: {
        "name": "Convenience Store",
        "size": 1,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x7F: {
        "name": "Gas Station 2",
        "size": 1,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x80: {
        "name": "Small Office Building 1",
        "size": 1,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x81: {
        "name": "Small Office Building 2",
        "size": 1,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x82: {
        "name": "Warehouse",
        "size": 1,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x83: {
        "name": "Cassidy’s Toy Store",
        "size": 1,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    # Industrial 1x1
    0x84: {
        "name": "Small WareHouse 1",
        "size": 1,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0x85: {
        "name": "Chemical Storage",
        "size": 1,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0x86: {
        "name": "Small WareHouse 2",
        "size": 1,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0x87: {
        "name": "Industral Substation",
        "size": 1,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    # misc. 1x1
    0x88: {
        "name": "Construction 7",
        "size": 1,
        "corners": True,
        "construction": True,
        "water": True,
        "power": True,
    },
    0x89: {
        "name": "Construction 8",
        "size": 1,
        "corners": True,
        "construction": True,
        "water": True,
        "power": True,
    },
    0x8A: {
        "name": "Abandoned Building 1",
        "size": 1,
        "corners": True,
        "abandoned": True,
        "water": True,
        "power": True,
    },
    0x8B: {
        "name": "Abandoned Building 2",
        "size": 1,
        "corners": True,
        "abandoned": True,
        "water": True,
        "power": True,
    },
    # Residential 2x2
    0x8C: {
        "name": "Cheap Apartments",
        "size": 2,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x8D: {
        "name": "Small Apartments 2",
        "size": 2,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x8E: {
        "name": "Small Apartments 3",
        "size": 2,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x8F: {
        "name": "Medium Apartments 1",
        "size": 2,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x90: {
        "name": "Medium Apartments 2",
        "size": 2,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x91: {
        "name": "Medium Condominiums 1",
        "size": 2,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x92: {
        "name": "Medium Condominiums 2",
        "size": 2,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0x93: {
        "name": "Medium Condominiums 3",
        "size": 2,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    # Commercial 2x2
    0x94: {
        "name": "Shopping Center",
        "size": 2,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x95: {
        "name": "Grocery Store",
        "size": 2,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x96: {
        "name": "Medium Office Building 1",
        "size": 2,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x97: {
        "name": "Resort hotel",
        "size": 2,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x98: {
        "name": "Medium Office Building 2",
        "size": 2,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x99: {
        "name": "Office/Retail",
        "size": 2,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x9A: {
        "name": "Medium Office Building 3",
        "size": 2,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x9B: {
        "name": "Medium Office Building 4",
        "size": 2,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x9C: {
        "name": "Medium Office Building 5",
        "size": 2,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0x9D: {
        "name": "Medium Office Building 6",
        "size": 2,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    # 2x2 Industrial
    0x9E: {
        "name": "Medium Warehouse",
        "size": 2,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0x9F: {
        "name": "Chemical Processing 2",
        "size": 2,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0xA0: {
        "name": "Small Factory 1",
        "size": 2,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0xA1: {
        "name": "Small Factory 2",
        "size": 2,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0xA2: {
        "name": "Small Factory 3",
        "size": 2,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0xA3: {
        "name": "Small Factory 4",
        "size": 2,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0xA4: {
        "name": "Small Factory 5",
        "size": 2,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0xA5: {
        "name": "Small Factory 6",
        "size": 2,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    # Misc 2x2
    0xA6: {
        "name": "Construction 3",
        "size": 2,
        "corners": True,
        "construction": True,
        "water": True,
        "power": True,
    },
    0xA7: {
        "name": "Construction 4",
        "size": 2,
        "corners": True,
        "construction": True,
        "water": True,
        "power": True,
    },
    0xA8: {
        "name": "Construction 5",
        "size": 2,
        "corners": True,
        "construction": True,
        "water": True,
        "power": True,
    },
    0xA9: {
        "name": "Construction 6",
        "size": 2,
        "corners": True,
        "construction": True,
        "water": True,
        "power": True,
    },
    0xAA: {
        "name": "Abandoned Building 3",
        "size": 2,
        "corners": True,
        "abandoned": True,
        "water": True,
        "power": True,
    },
    0xAB: {
        "name": "Abandoned Building 4",
        "size": 2,
        "corners": True,
        "abandoned": True,
        "water": True,
        "power": True,
    },
    0xAC: {
        "name": "Abandoned Building 5",
        "size": 2,
        "corners": True,
        "abandoned": True,
        "water": True,
        "power": True,
    },
    0xAD: {
        "name": "Abandoned Building 6",
        "size": 2,
        "corners": True,
        "abandoned": True,
        "water": True,
        "power": True,
    },
    # Residential 3x3
    0xAE: {
        "name": "Large Apartments 1",
        "size": 3,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0xAF: {
        "name": "Large Apartments 2",
        "size": 3,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0xB0: {
        "name": "Large Condominiums 1",
        "size": 3,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    0xB1: {
        "name": "Large Condominiums 2",
        "size": 3,
        "corners": True,
        "zone": "residential",
        "water": True,
        "power": True,
    },
    # commercial 3x3
    0xB2: {
        "name": "Office Park",
        "size": 3,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0xB3: {
        "name": "Office Tower 1",
        "size": 3,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0xB4: {
        "name": "Mini Mall",
        "size": 3,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0xB5: {
        "name": "Theater square",
        "size": 3,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0xB6: {
        "name": "Drive In",
        "size": 3,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0xB7: {
        "name": "Office Tower 2",
        "size": 3,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0xB8: {
        "name": "Office Tower 3",
        "size": 3,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0xB9: {
        "name": "Parking Lot",
        "size": 3,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0xBA: {
        "name": "Historic Office",
        "size": 3,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    0xBB: {
        "name": "Corporate Headquarters",
        "size": 3,
        "corners": True,
        "zone": "commercial",
        "water": True,
        "power": True,
    },
    # Industrial 3x3
    0xBC: {
        "name": "Chemical Processing",
        "size": 3,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0xBD: {
        "name": "Large Factory",
        "size": 3,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0xBE: {
        "name": "Industrial Thingamajig",
        "size": 3,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0xBF: {
        "name": "Medium Factory",
        "size": 3,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0xC0: {
        "name": "Large Warehouse 1",
        "size": 3,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    0xC1: {
        "name": "Large Warehouse 2",
        "size": 3,
        "corners": True,
        "zone": "industrial",
        "water": True,
        "power": True,
    },
    # Misc 3x3
    0xC2: {
        "name": "Construction 1",
        "size": 3,
        "corners": True,
        "construction": True,
        "water": True,
        "power": True,
    },
    0xC3: {
        "name": "Construction 2",
        "size": 3,
        "corners": True,
        "construction": True,
        "water": True,
        "power": True,
    },
    0xC4: {
        "name": "Abandoned Building 7",
        "size": 3,
        "corners": True,
        "abandoned": True,
        "water": True,
        "power": True,
    },
    0xC5: {
        "name": "Abandoned Building 8",
        "size": 3,
        "corners": True,
        "abandoned": True,
        "water": True,
        "power": True,
    },
    # Power Plants
    0xC6: {
        "name": "Hydoelectric Power Plant 1",
        "size": 1,
        "corners": True,
        "zone": "special",
        "power": True,
        "power_generated": True,
        "power_reported": 20,
        "microsim": "hydro",
        "cost": 400,
    },
    0xC7: {
        "name": "Hydoelectric Power Plant 2",
        "size": 1,
        "corners": True,
        "zone": "special",
        "power": True,
        "power_generated": True,
        "power_reported": 20,
        "microsim": "hydro",
        "cost": 400,
    },
    0xC8: {
        "name": "Wind Power Plant1",
        "size": 1,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "power_generated": True,
        "power_reported": 4,
        "microsim": "wind",
        "cost": 100,
    },
    0xC9: {
        "name": "Gas Power Plant",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "power_generated": True,
        "power_reported": 50,
        "microsim": "gas",
        "cost": 2000,
    },
    0xCA: {
        "name": "Oil Power Plant",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "power_generated": True,
        "power_reported": 220,
        "microsim": "oil",
        "cost": 6600,
    },
    0xCB: {
        "name": "Nuclear Power Plant",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "power_generated": True,
        "power_reported": 500,
        "microsim": "nuclear",
        "cost": 15000,
    },
    0xCC: {
        "name": "Solar Power Plant",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "power_generated": True,
        "power_reported": 50,
        "microsim": "solar",
        "cost": 1300,
    },
    0xCD: {
        "name": "Microwave Power Plant",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "power_generated": True,
        "power_reported": 1600,
        "microsim": "microwave",
        "cost": 28000,
    },
    0xCE: {
        "name": "Fusion Power Plant",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "power_generated": True,
        "power_reported": 2500,
        "microsim": "fusion",
        "cost": 40000,
    },
    0xCF: {
        "name": "Coal Power Plant",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "power_generated": True,
        "power_reported": 200,
        "microsim": "coal",
        "cost": 4000,
    },
    # Services/reward buildings
    0xD0: {
        "name": "City Hall",
        "size": 3,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "hall",
        "cost": 0,
    },
    0xD1: {
        "name": "Hospital",
        "size": 3,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "hospital",
        "cost": 500,
        "maintenance": 50,
    },
    0xD2: {
        "name": "Police Station",
        "size": 3,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "police",
        "cost": 500,
        "maintenance": 100,
    },
    0xD3: {
        "name": "Fire Station",
        "size": 3,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "fire",
        "cost": 500,
        "maintenance": 100,
    },
    0xD4: {
        "name": "Museum",
        "size": 3,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "museum",
        "cost": 1000,
    },
    0xD5: {
        "name": "Big Park",
        "size": 3,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "park",
        "cost": 150,
    },
    0xD6: {
        "name": "School",
        "size": 3,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "school",
        "cost": 250,
        "maintenance": 25,
    },
    0xD7: {
        "name": "Stadium",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "stadium",
        "cost": 0,
    },
    0xD8: {
        "name": "Prison",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "prison",
        "cost": 3000,
    },
    0xD9: {
        "name": "College",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "hospital",
        "cost": 1000,
        "maintenance": 100,
    },
    0xDA: {
        "name": "Zoo",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "zoo",
        "cost": 3000,
        "maintenance": 50,  # confirm
    },
    0xDB: {
        "name": "Statue",
        "size": 1,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "statue",
        "cost": 0,
    },
    # Infrastructure
    0xDC: {
        "name": "Water Pump",
        "size": 1,
        "corners": True,
        "zone": "special",
        "power": True,
        "water_produced": True,
        "underground": 0x1C,
        "cost": 100,
    },
    0xDD: {
        "name": "Runway",
        "size": 1,
        "corners": True,
        "zone": "airport",  # Also military, how to handle this?
        "power": True,
        "water": True,
    },
    0xDE: {
        "name": "Runway Intersection",
        "size": 1,
        "corners": True,
        "zone": "airport",  # Also military, how to handle this?
        "power": True,
        "water": True,
    },
    0xDF: {
        "name": "Seaport Pier",
        "size": 1,
        "zone": "Seaport",  # Also military, how to handle this?
    },
    0xE0: {
        "name": "Crane",
        "size": 1,
        "corners": True,
        "zone": "seaport",  # Also military, how to handle this?
        "power": True,
        "water": True,
    },
    0xE1: {
        "name": "Civilian Control Tower",
        "size": 1,
        "corners": True,
        "zone": "airpost",
        "power": True,
        "water": True,
    },
    0xE2: {
        "name": "Miliary Control Tower",
        "size": 1,
        "corners": True,
        "zone": "military",
        "power": True,
    },
    0xE3: {
        "name": "Warehouse",
        "size": 1,
        "corners": True,
        "zone": "seaport",  # Also military, how to handle this?
        "power": True,
        "water": True,
    },
    0xE4: {
        "name": "Airport Building 1",
        "size": 1,
        "corners": True,
        "zone": "airport",  # Also military, how to handle this?
        "power": True,
        "water": True,
    },
    0xE5: {
        "name": "Airport Building 1",
        "size": 1,
        "corners": True,
        "zone": "airport",  # Also military, how to handle this?
        "power": True,
        "water": True,
    },
    0xE6: {
        "name": "Tarmac",
        "size": 1,
        "corners": True,
        "zone": "airport",
        "power": True,
        "water": True,
    },
    0xE7: {
        "name": "F-15b",
        "size": 1,
        "corners": True,
        "zone": "military",
    },
    0xE8: {
        "name": "Military Hangar",
        "size": 1,
        "corners": True,
        "zone": "military",
    },
    0xE9: {
        "name": "Subway Station",
        "size": 1,
        "corners": True,
        "zone": "special",
        "power": True,
        "underground": 0x23,
        "cost": 250,
    },
    0xEA: {
        "name": "Radar",
        "size": 1,
        "corners": True,
        "zone": "airport",  # Also military, how to handle this?
        "power": True,
        "water": True,
    },
    0xEB: {
        "name": "Water Tower",
        "size": 2,
        "corners": True,
        "zone": "special",
        "power": True,
        "water_produced": True,
        "cost": 25,
    },
    0xEC: {
        "name": "Bus Depot",
        "size": 2,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "micosim": "bus",
        "cost": 250,
    },
    0xED: {
        "name": "Rail Depot",
        "size": 2,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "micosim": "rail",
        "cost": 500,
    },
    0xEE: {
        "name": "Civilian Parking Lot",
        "size": 2,
        "corners": True,
        "zone": "airport",
        "power": True,
        "water": True,
    },
    0xEF: {
        "name": "Military Parking Lot",
        "size": 2,
        "corners": True,
        "zone": "military",
    },
    0xF0: {
        "name": "Loading Bay",
        "size": 2,
        "corners": True,
        "zone": "seaport",
        "power": True,
        "water": True,
    },
    0xF1: {
        "name": "Top Secret",
        "size": 2,
        "corners": True,
        "zone": "military",
    },
    0xF2: {
        "name": "Cargo Yard",
        "size": 2,
        "corners": True,
        "zone": "seaport",  # Also military, how to handle this?
        "power": True,
        "water": True,
    },
    0xF3: {
        "name": "Mayor's House",
        "size": 2,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "mayor",
    },
    0xF4: {
        "name": "Water Treatment",
        "size": 2,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
    },
    0xF5: {
        "name": "Library",
        "size": 2,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "microsim": "library",
        "cost": 500,
    },
    0xF6: {
        "name": "Big Hangar",
        "size": 2,
        "corners": True,
        "zone": "airport",
        "power": True,
        "water": True,
    },
    0xF7: {
        "name": "Church",
        "size": 2,
        "corners": True,
        "power": True,
        "water": True,
    },
    0xF8: {
        "name": "Marina",
        "size": 3,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "cost": 1000,
    },
    0xF9: {
        "name": "Missile Silo",
        "size": 3,
        "corners": True,
        "zone": "military",
        "underground": 0x22,
    },
    0xFA: {
        "name": "Desalinization",
        "size": 3,
        "corners": True,
        "zone": "special",
        "power": True,
        "water_produced": True,
        "underground": 0x1C,
        "cost": 1000,
    },
    0xFB: {
        "name": "Plymouth Arcology",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "cost": 100000,
    },
    0xFC: {
        "name": "Forest Arcology",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "cost": 120000,
    },
    0xFD: {
        "name": "Darco",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "cost": 150000,
    },
    0xFE: {
        "name": "Launch Arcology",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "cost": 200000,
    },
    0xFF: {
        "name": "Braun Llama Dome",
        "size": 4,
        "corners": True,
        "zone": "special",
        "power": True,
        "water": True,
        "cost": 0,
    }
}


# Section with nice functions to access the data contained here.
def get_size(building_id):
    """
    Gets the size of a building given the building's ID.
    Args:
        building_id (int): id of the building.
    Returns:
        Either 1, 2, 3 or 4 depending on how large the building is.
    """
    return tile_data[building_id]["size"]


def get_name(building_id):
    """
    Gets the name of a building given the building's ID.
    Args:
        building_id (int): id of the building.
    Returns:
        String containing the building's name.
    """
    return tile_data[building_id]["name"]

# Tiles that can have a train sprite drawn on them:
train_tiles = [k for k, v in tile_data.items() if "Rail" in v["name"] and k not in (108, 109, 110, 111, 237)]