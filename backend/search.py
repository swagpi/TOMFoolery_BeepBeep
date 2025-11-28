import sqlite3
from typing import List

DB_PATH = "tomfoolery-rs-main/database.db"

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
