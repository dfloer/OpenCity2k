import argparse
import sys

sys.path.append('..')
import sc2_parse as sc2p


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest="input_file", help=".sc2 file top open and generate the report on", metavar="INFILE", required=True)
    args = parser.parse_args()
    return args


def convert_data(base_year, cycles):
    """
    Converts a data. Note that years have 300 days, which is divided into 12 months of 25 days each.
    Args:
        base_year (int): Year the city was started.
        cycles (int): days since the city was started.
    Returns:
        String date of the form "July 13, 2305"
    """
    year = (cycles // 300) + base_year
    days_passed_year = (cycles - ((year - base_year) * 300))
    month = days_passed_year // 25 + 1
    month_lookup = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}
    day = days_passed_year - ((month - 1) * 25) + 1
    return f"{month_lookup[month]} {day}, {year}"


if __name__ == "__main__":
    options = parse_command_line()
    filename = options.input_file
    city = sc2p.City()
    city.create_city_from_file(filename)
    weather_trend = {
        0x00: "Cold",
        0x01: "Clear",
        0x02: "Hot",
        0x03: "Foggy",
        0x04: "Chilly",
        0x05: "Overcast",
        0x06: "Snow",
        0x07: "Rain",
        0x08: "Windy",
        0x09: "Blizzard",
        0x0A: "Hurricane",
        0x0B: "Tornado",
    }
    graphs = ['City Size', 'Residents', 'Commerce', 'Industry', 'Traffic', 'Pollution', 'Value','Crime', 'Power %', 'Water %', 'Health', 'Education', 'Unemployment', 'GNP', "Nat'n Pop.", 'Fed Rate']
    print(f"City name: \"{city.city_name}\"")
    start_year = city.city_attributes["baseYear"]
    date = convert_data(start_year, city.city_attributes["simCycle"])
    print(f"Started in {start_year}, current date: {date}")
    print(f"Total population is {city.city_attributes['TotalPop']:,}, of which {city.city_attributes['GlobalArcoPop']:,} is from Arcologies.")
    print(f"Funding: ${city.city_attributes['TotalFunds']:,} and {50 - city.budget.bonds.count(0)} bonds.")
    print(f"Crimes: {city.city_attributes['CrimeCount']:,}, Traffic: {city.city_attributes['TrafficCount']:,}, Pollution: {city.city_attributes['Pollution']:,}.")
    print(f"City value: ${1000 * city.city_attributes['CityValue']:,}")
    print("\nOther stats:")
    print(f"The current weather is {weather_trend[city.city_attributes['weatherTrend']]}. Heat: {city.city_attributes['heat']}, Humidity: {city.city_attributes['humid']}, Wind: {city.city_attributes['wind']}.")
    print(f"{city.city_attributes['WorkerPercent']}% of the population is part of the workforce, with a life expectancy of {city.city_attributes['WorkerHealth']} years and EQ of {city.city_attributes['WorkerEducate']} and an unemployment rate of {city.city_attributes['unemployed']}%.")
    print(f"National Population is {1000 * city.city_attributes['NationalPop']:,} and national value is ${1000 * city.city_attributes['NationalValue']:,}.")
    print(f"\nGraph summary:")
    for g in graphs:
        print(f"\t{g}: {city.graphs[g].one_year[0]:,}")
