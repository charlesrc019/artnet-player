# Artnet Player 
Record and play ArtNet sequences from a web interface. 

## Description 
I'm a mobile DJ in my free time and have quite a bit of lighting equipment.
I wanted to be able to control my light shows remotely and record/playback some
of the more popular shows I've made, without having to be glued to the  lighting
console the whole time. The project glues together OLA and a Python web interface
to allow me to record and playback the DMX instructions like it is audio. 
  
## Dependencies 
`OLA` 
`Python3` 
`sqlite3` 
`tornado` 
`uuid`

## Instructions
This repository in pretty much plug-n-play. Just make sure you have the 
dependencies installed, and you should be good to go. One note is that, 
by default, the saved shows are stored in the data/ directory with a 
metadata SQLite database to keep track of everything.

## Options
- **port**: Adjust what port the server is listening on.
- **path**: Adjust the path where recordings and metadata are stored.
- **universe**: Adjust the ArtNet universes that OLA listens to and records.

