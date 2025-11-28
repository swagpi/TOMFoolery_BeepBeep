from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from map_data import handle_map_update_request, initialize_db
from search import search_stations as search_stations_func
from station_info import get_station_info

app = FastAPI(title="GTFS Map API")


DB_PATH = "tomfoolery-rs-main/database.db"
initialize_db(DB_PATH)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Request model
# -------------------------------
class MapRequest(BaseModel):
    north: float
    south: float
    east: float
    west: float
    buffer_meters: Optional[float] = 0
    max_stops: Optional[int] = 100


# -------------------------------
# API endpoints
# -------------------------------

#map data updates
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
        raise HTTPException(status_code=500, detail=str(e))

#search queries
@app.get("/search_stations")
def search_stations_api(query: str, limit: int = 20):
    return search_stations_func(query, limit)

#station information queries
@app.get("/station_info")
def station_info_endpoint(stop_id: str):
    return get_station_info(stop_id)
# -------------------------------
# Optional health check
# -------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}


# -------------------------------
# Run with: python api_server.py
# -------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
