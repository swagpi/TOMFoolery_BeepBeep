import sqlite3
from typing import Dict
from datetime import datetime, timedelta
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

def get_station_info(stop_id: str) -> Dict:
    """
    Fetch stop info and the next 100 trips including both scheduled and estimated arrival/departure times,
    removing duplicate trips.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Stop info
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

    # Current time in HHMMSS
    now_hhmmss = datetime.now().strftime("%H%M%S")

    # Scheduled trips after current time
    cur.execute("""
        SELECT t.trip_id, t.route_id, st.arrival_time, st.departure_time
        FROM stoptime st
        JOIN trip t ON st.trip_id = t.trip_id
        WHERE st.stop_id = ?
          AND st.arrival_time >= ?
    """, (stop_id, now_hhmmss))
    scheduled_trips_raw = [dict(row) for row in cur.fetchall()]

    # Remove duplicate trips (keep first occurrence)
    seen_trip_ids = set()
    scheduled_trips = []
    for trip in scheduled_trips_raw:
        if trip["trip_id"] not in seen_trip_ids:
            scheduled_trips.append(trip)
            seen_trip_ids.add(trip["trip_id"])

    # Live updates
    cur.execute("""
        SELECT trip_id, arrival_delay, departure_delay, shedule_status
        FROM trip_updates
        WHERE stop_id = ?
    """, (stop_id,))
    live_updates = {row["trip_id"]: dict(row) for row in cur.fetchall()}

    trips_with_estimates = []

    for trip in scheduled_trips:
        tid = trip["trip_id"]
        # Scheduled times
        scheduled_arrival = trip["arrival_time"]
        scheduled_departure = trip["departure_time"]

        # Default estimated times are the scheduled ones
        estimated_arrival = scheduled_arrival
        estimated_departure = scheduled_departure

        # Apply live delays if available
        if tid in live_updates:
            delay_info = live_updates[tid]
            arrival_delay_sec = int(delay_info.get("arrival_delay", 0))
            departure_delay_sec = int(delay_info.get("departure_delay", 0))

            # Convert HHMMSS to timedelta
            arr_h = int(scheduled_arrival[:2])
            arr_m = int(scheduled_arrival[2:4])
            arr_s = int(scheduled_arrival[4:6])
            dep_h = int(scheduled_departure[:2])
            dep_m = int(scheduled_departure[2:4])
            dep_s = int(scheduled_departure[4:6])

            estimated_arrival_dt = timedelta(hours=arr_h, minutes=arr_m, seconds=arr_s) + timedelta(seconds=arrival_delay_sec)
            estimated_departure_dt = timedelta(hours=dep_h, minutes=dep_m, seconds=dep_s) + timedelta(seconds=departure_delay_sec)

            # Convert back to HHMMSS
            def td_to_hhmmss(td: timedelta):
                total_sec = int(td.total_seconds()) % 86400
                h = total_sec // 3600
                m = (total_sec % 3600) // 60
                s = total_sec % 60
                return f"{h:02d}{m:02d}{s:02d}"

            estimated_arrival = td_to_hhmmss(estimated_arrival_dt)
            estimated_departure = td_to_hhmmss(estimated_departure_dt)

        trip.update({
            "scheduled_arrival": scheduled_arrival,
            "scheduled_departure": scheduled_departure,
            "estimated_arrival": estimated_arrival,
            "estimated_departure": estimated_departure,
        })
        trips_with_estimates.append(trip)

    # Sort by estimated arrival and take next 100
    trips_sorted = sorted(
        trips_with_estimates,
        key=lambda x: int(x["estimated_arrival"])
    )[:100]

    # Alerts relevant to this stop
    cur.execute("""
        SELECT header, description, cause, effect
        FROM alerts
        WHERE header LIKE ? OR description LIKE ?
    """, (f"%{stop_info['stop_name']}%", f"%{stop_info['stop_name']}%"))
    alerts = [dict(row) for row in cur.fetchall()]

    conn.close()

    return {
        "stop": stop_info,
        "next_trips": trips_sorted,
        "alerts": alerts
    }
