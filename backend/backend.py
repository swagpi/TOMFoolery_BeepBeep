from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import sys

# Helper modules (imported from existing files)
from map_data import handle_map_update_request, initialize_db
from search import search_stations as search_stations_func
from station_info import get_station_info
from station_to_path import get_routes_for_stop

app = FastAPI(title="GTFS Map API")

# -------------------------------
# 1. CORS SETTINGS (Crucial!)
# -------------------------------
# Allows Frontend (HTML) to access the Backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (For development)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS etc.)
    allow_headers=["*"],
)

# Database path
DB_PATH = "tomfoolery-rs-main/database.db" # Path to the DB created by Rust
# Attempt to initialize DB if it doesn't exist
try:
    initialize_db(DB_PATH)
    print(f"✅ Database initialized at: {DB_PATH}")
except Exception as e:
    print(f"⚠️ Database warning: {e}")

# -------------------------------
# Request Models
# -------------------------------
class MapRequest(BaseModel):
    north: float
    south: float
    east: float
    west: float
    buffer_meters: Optional[float] = 0
    max_stops: Optional[int] = 150

# -------------------------------
# API Endpoints
# -------------------------------

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Beep Beep Backend is Running! 🚌💨"}

# Map Data (Stops within bounds)
@app.post("/map_data")
def get_map_data(request: MapRequest):
    print(f"📥 Map Data Request: N={request.north}, S={request.south}")
    try:
        response = handle_map_update_request(
            DB_PATH,
            bounds=request.dict(),
            max_stops=request.max_stops
        )
        return response
    except Exception as e:
        print(f"❌ Error in /map_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Search Stations
@app.get("/search_stations")
def search_stations_api(query: str, limit: int = 20):
    print(f"🔍 Search Request: {query}")
    return search_stations_func(query, limit)

# Station Detail Info (Next Trips) - For Sidebar
@app.get("/station_info")
def station_info_endpoint(stop_id: str):
    print(f"🚏 Station Info Request for ID: {stop_id}")
    try:
        data = get_station_info(stop_id)
        return data
    except Exception as e:
        print(f"❌ Error in /station_info: {e}")
        return {"error": str(e), "next_trips": []}

# Full Route Path for a specific Trip
@app.get("/routes_for_stop")
def routes_for_stop_api(stop_id: str):
    print(f"🛣️ Route Request for stop_id={stop_id}")
    try:
        data = get_routes_for_stop(stop_id)
        return data
    except Exception as e:
        print(f"❌ Error in /routes_for_stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health Check
@app.get("/health")
def health_check():
    return {"status": "ok"}

# -------------------------------
# Execution
# -------------------------------
if __name__ == "__main__":
    print("🚀 Starting Backend Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)