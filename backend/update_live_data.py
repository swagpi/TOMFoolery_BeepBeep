from download_rt_gtfs_data import download_rt_gtfs_data
from map_data import update_live_data, initialize_db
from typing import Optional
import os
import sqlite3

DB_FILE_NAME = "/database.db"

def getDBPath() -> str:
    db_env: Optional[str] = os.getenv("DB_DIR")
    if db_env is None:
        return "tomfoolery-rs-main/database.db"
    else:
        return db_env + DB_FILE_NAME

DB_PATH = getDBPath()  # Path to the DB created by Rust

# --- Ensure necessary tables exist ---
def create_tables_if_not_exist(db_path: str):
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # Example: other_vehicles table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS other_vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT NOT NULL UNIQUE,
            form_factor TEXT,
            lat REAL,
            lon REAL,
            current_range_meters INTEGER,
            last_reported TEXT,
            rental_uris_web TEXT
        )
    """)

    # If you have more tables (like GTFS real-time tables), create them here
    # cur.execute("""
    # CREATE TABLE IF NOT EXISTS gtfs_vehicles (...);
    # """)

    con.commit()
    con.close()

initialize_db(DB_PATH)
# Create tables first
create_tables_if_not_exist(DB_PATH)

# Now update live data
update_live_data(DB_PATH, download_rt_gtfs_data())
