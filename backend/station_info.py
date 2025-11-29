import sqlite3
from typing import Dict
from datetime import datetime, timedelta

DB_PATH = "tomfoolery-rs-main/database.db"

def get_station_info(stop_id: str) -> Dict:
    """
    Fetch stop info and the next 100 trips.
    - Retrieves 'route_short_name' from the routes table.
    - Dynamically calculates the 'Last Stop' (Destination) for each trip.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Get Stop Details
    cur.execute("SELECT * FROM stops WHERE stop_id = ?", (stop_id,))
    stop_data = cur.fetchone()
    if not stop_data:
        conn.close()
        return {"error": "Stop not found"}
    stop_info = dict(stop_data)

    # Current time string
    now_hhmmss = datetime.now().strftime("%H%M%S")

    # 2. Fetch Scheduled Trips (With Route Name)
    # We use LEFT JOIN on 'routes' to get the name. 
    # If the table doesn't exist (older DB version), we handle the error.
    try:
        cur.execute("""
            SELECT 
                t.trip_id, 
                t.route_id, 
                st.arrival_time, 
                st.departure_time,
                r.route_short_name
            FROM stoptime st
            JOIN trip t ON st.trip_id = t.trip_id
            LEFT JOIN routes r ON t.route_id = r.route_id
            WHERE st.stop_id = ?
              AND st.arrival_time >= ?
        """, (stop_id, now_hhmmss))
    except sqlite3.OperationalError:
        # Fallback if 'routes' table is missing
        cur.execute("""
            SELECT t.trip_id, t.route_id, st.arrival_time, st.departure_time
            FROM stoptime st
            JOIN trip t ON st.trip_id = t.trip_id
            WHERE st.stop_id = ?
              AND st.arrival_time >= ?
        """, (stop_id, now_hhmmss))

    scheduled_trips_raw = [dict(row) for row in cur.fetchall()]

    # 3. Filter Duplicates & Prepare to find Destinations
    seen_trip_ids = set()
    scheduled_trips = []
    unique_trip_ids_list = []

    for trip in scheduled_trips_raw:
        if trip["trip_id"] not in seen_trip_ids:
            # Resolve Route Name
            # Use short_name if available, otherwise default to route_id
            route_name = trip.get("route_short_name")
            if not route_name:
                route_name = str(trip["route_id"])
            
            trip["display_route_name"] = route_name
            
            scheduled_trips.append(trip)
            seen_trip_ids.add(trip["trip_id"])
            unique_trip_ids_list.append(trip["trip_id"])

    # 4. Find Destination (Last Stop) for each trip
    trip_destinations = {}
    if unique_trip_ids_list:
        # We construct a query to find the stop name with the MAX sequence for each trip ID.
        id_list_str = ",".join("?" * len(unique_trip_ids_list))
        
        try:
            cur.execute(f"""
                SELECT st.trip_id, s.stop_name
                FROM stoptime st
                JOIN stops s ON st.stop_id = s.stop_id
                WHERE st.trip_id IN ({id_list_str})
                  AND st.stop_sequence = (
                      SELECT MAX(st2.stop_sequence) 
                      FROM stoptime st2 
                      WHERE st2.trip_id = st.trip_id
                  )
            """, unique_trip_ids_list)
            
            for row in cur.fetchall():
                trip_destinations[row["trip_id"]] = row["stop_name"]
        except Exception as e:
            print(f"⚠️ Error calculating destinations: {e}")

    # 5. Live Updates (Delays)
    live_updates = {}
    try:
        cur.execute("SELECT trip_id, arrival_delay FROM trip_updates WHERE stop_id = ?", (stop_id,))
        for row in cur.fetchall():
            live_updates[row["trip_id"]] = dict(row)
    except Exception:
        pass

    # 6. Final Merge
    final_trips = []
    for trip in scheduled_trips:
        tid = trip["trip_id"]
        
        # Assign Destination Name (Headsign)
        trip["display_headsign"] = trip_destinations.get(tid, "Unknown Destination")

        # Calculate Times
        scheduled_arrival = trip["arrival_time"]
        estimated_arrival = scheduled_arrival

        if tid in live_updates:
            delay = int(live_updates[tid].get("arrival_delay", 0))
            try:
                h = int(scheduled_arrival[:2])
                m = int(scheduled_arrival[2:4])
                s = int(scheduled_arrival[4:6])
                dt = timedelta(hours=h, minutes=m, seconds=s) + timedelta(seconds=delay)
                
                total_sec = int(dt.total_seconds()) % 86400
                eh = total_sec // 3600
                em = (total_sec % 3600) // 60
                es = total_sec % 60
                estimated_arrival = f"{eh:02d}{em:02d}{es:02d}"
            except:
                pass

        trip["estimated_arrival"] = estimated_arrival
        final_trips.append(trip)

    # Sort by Estimated Arrival Time
    trips_sorted = sorted(final_trips, key=lambda x: x["estimated_arrival"])[:100]

    conn.close()

    return {
        "stop": stop_info,
        "next_trips": trips_sorted
    }