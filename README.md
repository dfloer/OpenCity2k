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
 
 ## Utilies
 - None yet.