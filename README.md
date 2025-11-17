# Satellite Tracker

This is a program developed as part of my Honours project for my Bachelor of Computer Science. It is designed to take Two Line Element (TLE) data from a file or online and store it in an embeded SQLite database.
it can calculate the current and future positions of the satellites, display them in 2d and 3d, and also filter the list based on visability from any given location.

## User Guide
Dowload the code from the main branch, navigate to the root directory and run the following:
```
.\venv\Scripts\activate
pip install -r requirements.txt
```
The program can be started by running Main.py.

Add satellite data by importing a file or downloading data from CeresTrack using the built in query function

Satellites data will be displayed in the data table, and their location plotted on the globe and map visualisations

Regular satellite markers are red, if you click on a satellite in the table, it's marker will be highlighted in yellow. Clicking the 'Clear Selection' button will revert all the markers back to normal

The table can be filtered using the fields at the top of each column or sorted using the arrows in the header cells

The user can enter a pair of lattitude and longitude coordinates into the input fields above the charts to show only the satellites that are visible from that location. Clicking the 'Show All' button will remove this filter

The user can export satellite data to a file in Two Line Element (TLE) format by clicking the 'Export Data' button. the user can choose to export the entire database or just the current filtered list

Double clicking on a satellite will open up the details screen, where all the data associated with that satellite can be seen.

On the details screen, the user can enter a latitude and longitude to see if the satellite is currently visible, and using the slider to select a number of days can get a list of passes the satellite will make. This list can be exported to a csv file

The User can also enter a date, time, and timezone to get a predicted position of the satellite at that time. This future position is displayed on the charts in blue, and if the show path toggle is switched on, the path between the current position and the future position will be shown in green

The 'Delete All Satellites' button will delete all the satellites from the database 
