from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
from create_response import handle_map_update_request, initialize_db

app = FastAPI(title="GTFS Map API")

# Initialize database (adjust path to your DB)
DB_PATH = "tomfoolery-rs-main/database.db"
initialize_db(DB_PATH)

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
# API endpoint
# -------------------------------
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
