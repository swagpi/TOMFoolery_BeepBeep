# TOMFoolery_BeepBeep
# GTFS Map

This project provides a lightweight FastAPI backend for serving transit map data, station searches, and live trip information using a SQLite GTFS database that works with a simple frontend (we are not frontend devs) to give an easy to use integration of the app. 

---

## Features

### 🗺️ Map Data Retrieval
- Returns stops inside the current map bounds  
- Optional buffer (in meters) to enlarge the search area  
- Supports limiting the number of stops returned  for faster computing and better visibility

### 🔍 (Station) Search
- Full-text station search  
- Useful for autocompletion or global lookup
- Also works for any normal search e.g. restaurants  

### 🚏 Station Details
- Fetches all trips that pass through a stop  
- Includes:
  - Trip ID and route ID  
  - Ordered stop list for each trip  
  - Last known real-time stop (from `trip_updates`)  
  - Stop coordinates and name  

### ⚡ Real-Time Integration
- Reads `trip_updates` table to include approx. current vehicle position info  
- Allows for live information on any delays and alerts given by DB

### 🛴 Scooter Layer
- Map endpoint includes micromobility vehicles  
- shows estimated range based on open-source data provided by BW  

### 🛠️ Tech Stack
- FastAPI  
- SQLite (GTFS local database)  
- Pydantic  
- Uvicorn  
- CORS-enabled for browser clients  
- nginx
- systemd
- and probably some more I forgot

## Setup
To setup either run the installscript for debian and use the ./scripts/start_backend.py script to start the app
Otherwise run what is described in those scripts manually which is roughly execute the rust code in rust dir, run the initialisation python scripts and run the backend.py file to start the server

## Whats it actually usefull for?
The app allows access to the approximate realtime location based on all publicly available data for Germany which allows users to better gauge train delays, cancelations, ... compared to the DB app which gives very little info most times. It also integrates a live view for EScooters (with est. range) to combinde all kinds of public transport into one fast and easy app.

## Future?
In the future this app could also integrate a better path finding algorithm then the one right now to allow for better planning of trips, as well as live data on shared cars and bikes or uber and similar services to provide a all in one solution for the users mobility. **All this while staying open source and without any data tracking.**
