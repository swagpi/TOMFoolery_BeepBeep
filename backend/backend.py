from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Helper modules (from existing files)
from map_data import handle_map_update_request, initialize_db
from search import search_stations as search_stations_func
from station_info import get_station_info
from station_to_path import get_routes_for_stop

app = FastAPI(title="GTFS Map API")

# -------------------------------
# 1. CORS SETTINGS (Very Important!)
# -------------------------------
# Without this setting, Frontend (HTML) cannot access Backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (For development phase)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],
)

# Database path
DB_PATH = "tomfoolery-rs-main/database.db" # DB path created by the Rust project
# Try to create DB if it doesn't exist (Optional, usually handled by Rust side)
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

# Root endpoint (Runs when http://localhost:8000 is opened in browser)
@app.get("/")
def read_root():
    return {"message": "Beep Beep Backend is Running! 🚌💨"}

# Map Data (Stops)
@app.post("/map_data")
def get_map_data(request: MapRequest):
    try:
        response = handle_map_update_request(
            DB_PATH,
            bounds=request.dict(),
            max_stops=request.max_stops
        )
        return response
    except Exception as e:
        print(f"❌ Error in /map_data: {e}")
        # Return empty data or raise error to prevent frontend crash
        raise HTTPException(status_code=500, detail=str(e))

# Search
@app.get("/search_stations")
def search_stations_api(query: str, limit: int = 20):
    print(f"🔍 Search Request: {query}")
    return search_stations_func(query, limit)

# Stop Detail Info (Trips) - For Sidebar
@app.get("/station_info")
def station_info_endpoint(stop_id: str):
    print(f"🚏 Station Info Request for ID: {stop_id}")
    try:
        data = get_station_info(stop_id)
        return data
    except Exception as e:
        print(f"❌ Error in /station_info: {e}")
        return {"error": str(e), "next_trips": []}

@app.get("/routes_for_stop")
def routes_for_stop_api(stop_id: int):
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