from download_rt_gtfs_data import download_rt_gtfs_data
from map_data import update_live_data
from typing import Optional
import os

DB_FILE_NAME = "/database.db"

def getDBPath() -> str:
    db_env: Optional[str] = os.getenv("DB_DIR")
    if db_env is None:
        return "tomfoolery-rs-main/database.db"
    else:
        return db_env + DB_FILE_NAME

DB_PATH = getDBPath() # Path to the DB created by Rust

update_live_data(DB_PATH, download_rt_gtfs_data())
