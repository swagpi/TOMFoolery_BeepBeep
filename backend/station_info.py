import sqlite3
from typing import Dict
from datetime import datetime, timedelta

# DB_PATH = "tomfoolery-rs-main/database.db"

def get_station_info(stop_id: int, db_path: str) -> Dict:
    """
    Fetch stop info and the next 100 trips including scheduled/estimated times,
    route short names, and trip headsigns.
    """
    conn = sqlite3.connect(db_path)
    print("Connected to database")
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
    # NOTE: We assume 'route' table and 'trip_headsign' column exist in your DB.
    # If your Rust importer didn't create them, this might need adjustment.

    cur.execute("""
        SELECT trip_id, arrival_time, departure_time
        FROM stoptime
        WHERE stop_id = ? AND arrival_time >= ?
    """, (stop_id, now_hhmmss))
    scheduled_trips_raw = [dict(row) for row in cur.fetchall()]

    trip_ids = []
    for trip in scheduled_trips_raw:
        trip_ids.append(trip["trip_id"])

    trip_ids_substitution_string = ",".join("?" for _ in trip_ids)
    print(trip_ids_substitution_string)

    cur.execute(f"""
    SELECT t.trip_id, r.route_short_name
    FROM trip t
    JOIN routes r ON t.route_id = r.route_id
    WHERE t.trip_id IN ({trip_ids_substitution_string});
    """, trip_ids)
    
    trip_id_route_name_list = cur.fetchall()

    trip_to_shortname_dict = { trip_id: short for trip_id, short in trip_id_route_name_list }

    # Remove duplicate trips (keep first occurrence)

    seen_trip_ids = set()
    scheduled_trips = []
    for trip in scheduled_trips_raw:
        trip_id = trip["trip_id"]
        if trip["trip_id"] not in seen_trip_ids:
            # --- LOGIC FOR DISPLAY NAMES ---
            # Route Name: Short > Long > ID
            # route_name = trip.get("route_short_name") or trip.get("route_long_name") or str(trip["route_id"])

            trip["display_route_name"] = trip_to_shortname_dict[trip_id]
            scheduled_trips.append(trip)
            seen_trip_ids.add(trip_id)



    # Live updates
    try:
        cur.execute("""
            SELECT trip_id, arrival_delay, departure_delay
            FROM trip_updates
            WHERE stop_id = ?
        """, (stop_id,))
        live_updates = {row["trip_id"]: dict(row) for row in cur.fetchall()}
    except Exception:
        live_updates = {}

    trips_with_estimates = []

    for trip in scheduled_trips:
        tid = trip["trip_id"]
        scheduled_arrival = trip["arrival_time"]
        scheduled_departure = trip["departure_time"]
        
        # Default estimates
        estimated_arrival = scheduled_arrival
        estimated_departure = scheduled_departure

        # Apply live delays
        if tid in live_updates:
            delay_info = live_updates[tid]
            arrival_delay = int(delay_info.get("arrival_delay", 0))
            departure_delay = int(delay_info.get("departure_delay", 0))
            
            try:
                # Simple HHMMSS parsing
                h = int(scheduled_arrival[:2])
                m = int(scheduled_arrival[2:4])
                s = int(scheduled_arrival[4:6])
                
                dt = timedelta(hours=h, minutes=m, seconds=s) + timedelta(seconds=arrival_delay)
                
                total_seconds = int(dt.total_seconds()) % 86400
                eh = total_seconds // 3600
                em = (total_seconds % 3600) // 60
                es = total_seconds % 60
                estimated_arrival = f"{eh:02d}{em:02d}{es:02d}"
            except ValueError:
                pass

        trip.update({
            "estimated_arrival": estimated_arrival,
            "estimated_departure": estimated_departure,
        })
        trips_with_estimates.append(trip)

    # Sort by time
    trips_sorted = sorted(trips_with_estimates, key=lambda x: x["estimated_arrival"])[:100]

    conn.close()

    return {
        "stop": stop_info,
        "next_trips": trips_sorted
    }
