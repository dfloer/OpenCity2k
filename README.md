# OpenCity2k
The goal of this project is to have a free/open source re-implementation of SimCity 2000 as well as various bugfixes and enhancements including infinite cities, more graphical customization, more types of networks, more buildings, history tracking/replays, multiplayer support and more.

Documentation of the various binary file formats and of the simulation behaviour can be found at [https://github.com/dfloer/SC2k-docs].

## Project Structure
### Server
This runs the simulation directly and handles updates to the client. Written in Python. This model was chosen to make future multiplayer support easier.
### Client
Contains the game engine and code for communicating with the server. Likely written in something better suited for game development, though kivy(kivent) and Panda3D are engine options. 

## Current Status
Implementing basic functionality and parsing of game assets. Initial focus is around parsing .sc2 city files, .mif tilesets, .scn scenarios as well as all game assets, which will need to be sourced independently of this project as EA still claims copyright on them.

Initial foc

## Requirements
 - pillow
 - python 3.6+
 
## Currently supported features.
 - Opening and uncompressing city files.
 - Saving uncompressed and compressed city files.
 - Parsing the TEXT_USA files.
 - Parsing SMALLMED.DAT, SPECIAL.DAT and LARGE.DAT sprite data files.
 - Parsing MIFF files.
 
## Utilities
 - text_usa_parse.py: Extracts the contents of TEXT_USA.DAT. Currently very raw output.
    - `-d/--data`: the path to TEXT_USA.DAT
    - `-i/--index`: the path to TEXT_USA.IDX
    - `-t/--text`: optional path for exported text file. Omitting this will write to stdout.
    
  - tileset_parse.py: Extracts the contents of LARGE.DAT, SMALLMED.DAT and SPECIAL.DAT and saves them as either PNGs, or animated gifs of the colour cycling animation.
    - `-i/--input`: Path to the directory containing the 3 data files.
    - `-o/--output`: Path to the directory to save output in.
    - `-p/--palette`: Path to the file containing the palette to load. Note that this will likely be `PAL_MSTR.BMP`.
    - `-w/--write-palette`: Path and filename for the palette to be written to. Useful for debugging.
    - `-a/--animate`: Create animated gifs of each sprite, using the game's colour cycling system for basic animations. Saved in the same output folder as specificed in `-o/--output`.
    - `-d/--dump`: Most useful for debugging, dumps each raw frame for the animation. Saved in same output folder as animations are.
- miff_parse.py: Turns the contents of a .mif file into their sprites, much like tileset_parse.py does.
    - `-i/--input`: Path to the directory containing the 3 data files.
    - `-o/--output`: Path to the directory to save output in.
    - `-p/--palette`: Path to the file containing the palette to load.
    - `-a/--animate`: Create animated gifs of each sprite, using the game's colour cycling system for basic animations. Saved in the same output folder as specificed in `-o/--output`.
