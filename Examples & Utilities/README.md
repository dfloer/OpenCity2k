# Examples & Utilities
This folder contains some examples and utilities that do useful things and also illustrate how to manipulate city data.

## Things
 - `city_report.py`: Command line utility to print a summary of the city to stdout.\
    Args:
   - `-i`/`--input`: input .sc2 to open and generate the report on.
 - `city_preview.py`: Command line utility to create a full-resolution preview image of a city.\
    Args:
    - `-i`/`--input`: input .sc2 to open and generate the image of.
    - `-o`/`--output`: where to save the output png. Just the filename, will append extension itself.
    - `-s`/`--sprites`: directory containing the sprites. Currently only works with large (32 x 17px tile size) sprites. These can be generates using `sprite_parse.py`.
    - `-t`/`--transparent`: if set, draw city with a transparent background.