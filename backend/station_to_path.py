import sqlite3

DB_PATH = "tomfoolery-rs-main/database.db"


def get_routes_for_stop(stop_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ------------------------------------
    # 1. Find all trips that pass through this stop
    # ------------------------------------
    cur.execute("""
        SELECT t.trip_id, t.route_id, st.stop_sequence
        FROM stoptime st
        JOIN trip t ON st.trip_id = t.trip_id
        WHERE st.stop_id = ?
        ORDER BY t.route_id, t.trip_id, st.stop_sequence
    """, (stop_id,))

    rows = cur.fetchall()
    if not rows:
        conn.close()
        return []

    # Remove duplicates (route_id + trip_id)
    seen = set()
    trips = []
    for trip_id, route_id, stop_seq in rows:
        if trip_id not in seen:
            seen.add(trip_id)
            trips.append((trip_id, route_id, stop_seq))

    trip_ids = tuple(t[0] for t in trips)

    # ------------------------------------
    # 2. Load all stoptimes for all trips at once
    # ------------------------------------
    cur.execute(f"""
        SELECT st.trip_id, st.stop_id, st.stop_sequence
        FROM stoptime st
        WHERE st.trip_id IN ({",".join("?" * len(trip_ids))})
        ORDER BY st.trip_id, st.stop_sequence
    """, trip_ids)

    stoptime_rows = cur.fetchall()

    # Group by trip_id
    trip_stops_map = {}
    for trip_id, sid, seq in stoptime_rows:
        trip_stops_map.setdefault(trip_id, []).append((sid, seq))

    # ------------------------------------
    # 3. Load stop details only once
    # ------------------------------------
    all_stop_ids = list({sid for _, sid, _ in stoptime_rows})
    cur.execute(f"""
        SELECT stop_id, stop_name, latitude, longitude
        FROM stops
        WHERE stop_id IN ({",".join("?" * len(all_stop_ids))})
    """, all_stop_ids)

    stop_info_map = {
        sid: {"stop_id": sid, "name": name, "lat": lat, "lon": lon}
        for sid, name, lat, lon in cur.fetchall()
    }

    # ------------------------------------
    # 4. Load last known positions from trip_updates
    # ------------------------------------
    cur.execute(f"""
        SELECT trip_id, stop_id
        FROM trip_updates
        WHERE trip_id IN ({",".join("?" * len(trip_ids))})
        ORDER BY trip_id
    """, trip_ids)

    updates = {}
    for trip_id, current_stop in cur.fetchall():
        updates[trip_id] = current_stop

    conn.close()

    # ------------------------------------
    # 5. Build final structured response
    # ------------------------------------
    results = []

    for trip_id, route_id, stop_seq in trips:
        stops_for_trip = trip_stops_map.get(trip_id, [])

        full_stops = []
        for sid, seq in stops_for_trip:
            info = stop_info_map.get(sid)
            if info:
                full_stops.append({
                    "stop_id": sid,
                    "sequence": seq,
                    "name": info["name"],
                    "lat": info["lat"],
                    "lon": info["lon"]
                })

        current_real_stop = updates.get(trip_id)

        results.append({
            "trip_id": trip_id,
            "route_id": route_id,
            "current_stop_sequence": stop_seq,
            "last_known_stop": current_real_stop,
            "full_route_stops": full_stops
        })

    return results