import sqlite3

DB_PATH = "tomfoolery-rs-main/database.db"


def get_routes_for_stop(stop_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Fast bulk query for all needed data
    cur.execute("""
        SELECT 
            t.trip_id,
            t.route_id,
            st_main.stop_sequence AS current_seq,

            st_all.stop_id,
            st_all.stop_sequence,
            s.stop_name,
            s.latitude,
            s.longitude

        FROM stoptime st_main
        JOIN trip t ON st_main.trip_id = t.trip_id
        JOIN stoptime st_all ON st_all.trip_id = t.trip_id
        JOIN stops s ON st_all.stop_id = s.stop_id

        WHERE st_main.stop_id = ?

        ORDER BY t.route_id, t.trip_id, st_all.stop_sequence
    """, (stop_id,))

    rows = cur.fetchall()
    if not rows:
        conn.close()
        return []

    # 2. Load all updates once
    cur.execute("SELECT trip_id, stop_id FROM trip_updates")
    updates_raw = cur.fetchall()

    conn.close()

    trip_updates = {trip_id: next_stop_id for trip_id, next_stop_id in updates_raw}

    # 3. Build structured result
    trips = {}
    seen = set()

    for (
        trip_id, route_id, current_seq,
        sid, seq, name, lat, lon
    ) in rows:

        if trip_id not in trips:
            trips[trip_id] = {
                "trip_id": trip_id,
                "route_id": route_id,
                "current_stop_sequence": current_seq,
                "full_route_stops": [],
                "last_stop": None     # <- filled later
            }

        key = (trip_id, sid, seq)
        if key in seen:
            continue
        seen.add(key)

        trips[trip_id]["full_route_stops"].append({
            "stop_id": sid,
            "sequence": seq,
            "name": name,
            "lat": lat,
            "lon": lon
        })

    # 4. For each active trip, determine the **last completed stop**
    for trip_id, data in trips.items():
        if trip_id not in trip_updates:
            continue  # not active right now

        next_stop_id = trip_updates[trip_id]

        # find next stop sequence
        next_stop = next((s for s in data["full_route_stops"] if s["stop_id"] == next_stop_id), None)
        if not next_stop:
            continue  # skip trip with corrupted update

        next_seq = next_stop["sequence"]
        last_seq = next_seq - 1

        # find last stop in ordered stop list
        last_stop = next((s for s in data["full_route_stops"] if s["sequence"] == last_seq), None)

        data["last_stop"] = last_stop  # may be None if trip hasn't started yet

    return list(trips.values())


if __name__ == "__main__":
    import json
    print(json.dumps(get_routes_for_stop(379640)[:2], indent=2))
