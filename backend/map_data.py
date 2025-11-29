import sqlite3
import time

def initialize_db(db_path: str):
    """
    Creates tables and indexes if they don't exist.
    Run this once after building or recreating the database.
    """
    print("attempting to open db at:",db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stops(
            stop_name TEXT,
            longitude REAL,
            latitude REAL,
            stop_id INTEGER PRIMARY KEY,
            location_type INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trip(
            route_id INTEGER,
            service_id INTEGER,
            trip_id INTEGER PRIMARY KEY
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stoptime(
            trip_id INTEGER,
            arrival_time TEXT,
            departure_time TEXT,
            stop_id INTEGER,
            stop_sequence INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS service(
            mon INTEGER, tue INTEGER, wed INTEGER, thur INTEGER, fri INTEGER,
            sat INTEGER, sun INTEGER, start_date INTEGER, end_date INTEGER, service_id INTEGER PRIMARY KEY
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trip_updates(
            schedule_status INTEGER,
            trip_id TEXT,
            stop_id TEXT,
            arrival_delay INTEGER,
            departure_delay INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts(
            header TEXT, description TEXT, cause INTEGER, effect INTEGER
        )
    """)

    # Create indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stops_lat_lon ON stops(latitude, longitude)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stoptime_trip_id ON stoptime(trip_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stoptime_stop_id ON stoptime(stop_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stoptime_trip_sequence ON stoptime(trip_id, stop_sequence)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trip_trip_id ON trip(trip_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trip_route_id ON trip(route_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trip_updates_trip ON trip_updates(trip_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_trip_updates_stop ON trip_updates(stop_id)")

    conn.commit()
    conn.close()


def update_live_data(database_path: str, rt_updates):
    """
    Inserts live GTFS updates into trip_updates and alerts tables.
    Wraps in a transaction for speed.
    """
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()

    cur.execute("DELETE FROM trip_updates")
    cur.execute("DELETE FROM alerts")

    with conn:
        cur.executemany(
            "INSERT INTO trip_updates(trip_id, stop_id, arrival_delay, departure_delay) VALUES (?,?,?,?)",
            rt_updates[1]
        )
        cur.executemany(
            "INSERT INTO alerts(header, description, cause, effect) VALUES (?,?,?,?)",
            rt_updates[2]
        )

    conn.close()


def handle_map_update_request(db_path, bounds, max_stops=100):
    """
    Fetch stops and routes within a map area (with optional buffer), sample stops,
    fetch representative trips per route, and return structured JSON response.
    """
    t0 = time.time()
    north, south, east, west = bounds["north"], bounds["south"], bounds["east"], bounds["west"]
    buffer_meters = bounds.get("buffer_meters", 0)

    if north-south > 0.1:
        return {"type": "MapDataResponse", "payload": {"stops": [], "routes": []}}


    #print(f"North {north}, South {south}, West {west}, east {east}")

    # Convert buffer meters to degrees
    deg_buf = buffer_meters / 111_320
    north += deg_buf
    south -= deg_buf
    east += deg_buf
    west -= deg_buf

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch stops inside bounds
    cur.execute("""
        SELECT stop_id, stop_name, latitude, longitude
        FROM stops
        WHERE latitude BETWEEN ? AND ?
          AND longitude BETWEEN ? AND ?
    """, (south, north, west, east))
    all_stops = [dict(row) for row in cur.fetchall()]
    if not all_stops:
        conn.close()
        return {"type": "MapDataResponse", "payload": {"stops": [], "routes": []}}

    # Randomly sample stops if too many
    #stops = random.sample(all_stops, max_stops) if len(all_stops) > max_stops else all_stops
    stops = all_stops
    stop_ids_in_area = {s["stop_id"] for s in stops}
    routes = []

    cur.execute("""
        SELECT vehicle_id, lat AS latitude, lon AS longitude, form_factor
        FROM other_vehicles
        WHERE lat BETWEEN ? AND ?
          AND lon BETWEEN ? AND ?
    """, (south, north, west, east))
    escooters = [dict(row) for row in cur.fetchall()]
    print(escooters)

    return {"type": "MapDataResponse", "payload": {"stops": stops, "routes": routes, "escooters": escooters}}

    # Temp table for sampled stops
    cur.execute("CREATE TEMP TABLE tmp_stops(stop_id INT)")
    cur.executemany("INSERT INTO tmp_stops(stop_id) VALUES (?)", [(s,) for s in stop_ids_in_area])

    # Fetch all trip_ids visiting these stops
    cur.execute("""
        SELECT DISTINCT st.trip_id
        FROM stoptime st
        JOIN tmp_stops ts ON st.stop_id = ts.stop_id
        LIMIT 100
    """)
    trip_ids = [row["trip_id"] for row in cur.fetchall()]
    if not trip_ids:
        conn.close()
        return {"type": "MapDataResponse", "payload": {"stops": stops, "routes": []}}

    # Temp table for trips
    cur.execute("CREATE TEMP TABLE tmp_trips(trip_id INT)")
    cur.executemany("INSERT INTO tmp_trips(trip_id) VALUES (?)", [(t,) for t in trip_ids])

    # Fetch unique route_ids with one representative trip per route
    cur.execute("""
        SELECT route_id, MIN(trip_id) AS rep_trip_id
        FROM trip
        WHERE trip_id IN (SELECT trip_id FROM tmp_trips)
        GROUP BY route_id
        LIMIT 100
    """)
    rep_trips = {row["route_id"]: row["rep_trip_id"] for row in cur.fetchall()}

    # Fetch all stop sequences for representative trips in bulk
    rep_trip_ids = list(rep_trips.values())
    if rep_trip_ids:
        q_marks = ",".join("?" * len(rep_trip_ids))
        cur.execute(f"""
            SELECT st.trip_id, st.stop_id, s.latitude, s.longitude
            FROM stoptime st
            JOIN stops s ON st.stop_id = s.stop_id
            WHERE st.trip_id IN ({q_marks})
            ORDER BY st.trip_id, st.stop_sequence
            LIMIT 100
        """, tuple(rep_trip_ids))

        stops_by_trip = {}
        for row in cur.fetchall():
            tid = row["trip_id"]
            stops_by_trip.setdefault(tid, []).append({"stop_id": row["stop_id"]})
    else:
        stops_by_trip = {}

    # Build route responses
    routes = []
    for route_id, rep_trip_id in rep_trips.items():
        routes.append({
            "route_id": route_id,
            "trip_id": rep_trip_id,
            "stops": stops_by_trip.get(rep_trip_id, [])
        })

    # Cleanup temp tables
    cur.execute("DROP TABLE IF EXISTS tmp_stops")
    cur.execute("DROP TABLE IF EXISTS tmp_trips")
    conn.close()

    print(f"Map request handled in {time.time() - t0:.2f} seconds")
    return {"type": "MapDataResponse", "payload": {"stops": stops, "routes": routes}}
