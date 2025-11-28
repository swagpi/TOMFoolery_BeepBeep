from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Helper modüller (mevcut dosyalarından)
from map_data import handle_map_update_request, initialize_db
from search import search_stations as search_stations_func
from station_info import get_station_info
from station_to_path import get_routes_for_stop

app = FastAPI(title="GTFS Map API")

# -------------------------------
# 1. CORS AYARLARI (Çok Önemli!)
# -------------------------------
# Bu ayar olmadan Frontend (HTML) Backend'e erişemez.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm kaynaklara izin ver (Geliştirme aşaması için)
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, OPTIONS vb. hepsine izin ver
    allow_headers=["*"],
)

# Veritabanı yolu
DB_PATH = "tomfoolery-rs-main/database.db" # Rust projesinin oluşturduğu DB yolu
# Eğer DB yoksa oluşturmayı dene (Opsiyonel, genelde Rust tarafı halleder)
try:
    initialize_db(DB_PATH)
    print(f"✅ Database initialized at: {DB_PATH}")
except Exception as e:
    print(f"⚠️ Database warning: {e}")

# -------------------------------
# Request Modelleri
# -------------------------------
class MapRequest(BaseModel):
    north: float
    south: float
    east: float
    west: float
    buffer_meters: Optional[float] = 0
    max_stops: Optional[int] = 150

# -------------------------------
# API Endpointleri
# -------------------------------

# Root endpoint (Tarayıcıda http://localhost:8000 açınca çalışır)
@app.get("/")
def read_root():
    return {"message": "Beep Beep Backend is Running! 🚌💨"}

# Harita Verisi (Duraklar)
@app.post("/map_data")
def get_map_data(request: MapRequest):
    print("request: ", request)
    print(f"📥 Map Data Request: N={request.north}, S={request.south}")
    try:
        response = handle_map_update_request(
            DB_PATH,
            bounds=request.dict(),
            max_stops=request.max_stops
        )
        print("Response: ", response)
        return response
    except Exception as e:
        print(f"❌ Error in /map_data: {e}")
        # Frontend çökmesin diye boş veri dönelim veya hata fırlatalım
        raise HTTPException(status_code=500, detail=str(e))

# Arama (Search)
@app.get("/search_stations")
def search_stations_api(query: str, limit: int = 20):
    print(f"🔍 Search Request: {query}")
    return search_stations_func(query, limit)

# Durak Detay Bilgisi (Seferler) - Sidebar için
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

# Sağlık Kontrolü
@app.get("/health")
def health_check():
    return {"status": "ok"}

# -------------------------------
# Çalıştırma
# -------------------------------
if __name__ == "__main__":
    print("🚀 Starting Backend Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)