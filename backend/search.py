import sqlite3
from typing import List
from typing import Optional
import os

DB_FILE_NAME: str = "/database.db"
def getDBPath() -> str:
    db_env: Optional[str] = os.getenv("DB_DIR")
    if db_env is None:
        return "tomfoolery-rs-main/database.db"
    else:
        return db_env + DB_FILE_NAME

DB_PATH = getDBPath()

def search_stations(query: str, limit: int = 20) -> List[dict]:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("""
        SELECT stop_id, stop_name, latitude, longitude
        FROM stops
        WHERE stop_name LIKE ?
        ORDER BY stop_name
        LIMIT ?
    """, (f"%{query}%", limit))
    results = [dict(row) for row in cur.fetchall()]
    con.close()
    return results
