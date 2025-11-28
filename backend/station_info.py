import sqlite3
from typing import Dict

DB_PATH = "tomfoolery-rs-main/database.db"

def get_station_info(stop_id: str) -> Dict:
    """
    Fetches static stop info, scheduled trips, live updates, and alerts for a given stop_id.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Static stop info
    cur.execute("""
        SELECT stop_id, stop_name, latitude, longitude, location_type
        FROM stops
        WHERE stop_id = ?
    """, (stop_id,))
    stop_data = cur.fetchone()
    if not stop_data:
        conn.close()
        return {"error": "Stop not found"}
    stop_info = dict(stop_data)

    # Scheduled trips
    cur.execute("""
        SELECT t.trip_id, t.route_id, st.arrival_time, st.departure_time
        FROM stoptime st
        JOIN trip t ON st.trip_id = t.trip_id
        WHERE st.stop_id = ?
        ORDER BY st.arrival_time
    """, (stop_id,))
    scheduled_trips = [dict(row) for row in cur.fetchall()]

    # Live updates
    cur.execute("""
        SELECT trip_id, arrival_delay, departure_delay, shedule_status
        FROM trip_updates
        WHERE stop_id = ?
    """, (stop_id,))
    live_updates = {row["trip_id"]: dict(row) for row in cur.fetchall()}

    # Merge live updates into scheduled trips
    for trip in scheduled_trips:
        tid = trip["trip_id"]
        if tid in live_updates:
            trip.update(live_updates[tid])

    # Alerts
    cur.execute("""
        SELECT header, description, cause, effect
        FROM alerts
        WHERE header LIKE ? OR description LIKE ?
    """, (f"%{stop_info['stop_name']}%", f"%{stop_info['stop_name']}%"))
    alerts = [dict(row) for row in cur.fetchall()]

    conn.close()

    return {
        "stop": stop_info,
        "trips": scheduled_trips,
        "alerts": alerts
    }
