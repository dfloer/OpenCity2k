# Examples & Utilities
This folder contains some examples and utilities that do useful things and also illustrate how to manipulate city data.

## Things
 - `city_report.py`: Command line utility to print a summary of the city to stdout.

    Command line arguments:
   - `-i`/`--input`: input .sc2 to open and generate the report on.
 - `city_preview.py`: Command line utility to create a full-resolution preview image of a city.\
    Currently very much a work in progress, but the basics of rendering a city mostly work.

    Command line arguments:
    - `-i`/`--input`: input .sc2 to open and generate the image of.
    - `-o`/`--output`: where to save the output png. Just the filename, will append extension itself.
    - `-s`/`--sprites`: directory containing the sprites. Currently only works with large (32 x 17px tile size) sprites. These can be generates using `sprite_parse.py`.
    - `-t`/`--transparent`: if set, draw city with a transparent background.

 - `city_minimaps.py`: Command line utility to generate minimaps for a city, kinda like the ones in the game. Note that the minimaps in the game aren't 128x128, but are scaled by the UI. This generates square 128x128 minimaps.

    Command line arguments:
   - `-i`/`--input`: input .sc2 to open and generate the minimaps on.
   - `-o`/`--output`: Directory to create the minimaps in.
   - `-p`/`--palette`: Full path to the `PAL_MSTR.BMP` file to use for the palette.

Currently generated minimaps:
   - Structures: Only shows where structures are, base minimap in game.
   - Zones: shows zones.
