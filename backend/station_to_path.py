import sqlite3
from fastapi import HTTPException
from typing import List, Dict

DB_PATH = "tomfoolery-rs-main/database.db"


def get_routes_for_stop(stop_id: str) -> List[Dict]:
    """
    Fetch all routes that include a given stop, along with trips and stops on each trip.

    Returns a list of dictionaries:
    [
        {
            "route_id": "route123",
            "route_name": "Route Name",
            "trips": [
                {
                    "trip_id": "trip456",
                    "current_stop_index": 3,
                    "stops_on_route": [
                        {"stop_id": "stop1", "stop_sequence": 1},
                        {"stop_id": "stop2", "stop_sequence": 2},
                        ...
                    ]
                },
                ...
            ]
        },
        ...
    ]
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Find all trips that include this stop
    cur.execute("""
        SELECT t.trip_id, t.route_id, st.stop_sequence
        FROM stoptime st
        JOIN trip t ON st.trip_id = t.trip_id
        WHERE st.stop_id = ?
        ORDER BY t.route_id, t.trip_id, st.stop_sequence
    """, (stop_id,))
    stop_times_rows = cur.fetchall()

    if not stop_times_rows:
        conn.close()
        raise HTTPException(status_code=404, detail=f"No trips found for stop {stop_id}")

    # Group trips by route
    routes_dict = {}
    for row in stop_times_rows:
        route_id = row['route_id']
        trip_id = row['trip_id']
        stop_seq_at_current = row['stop_sequence']

        if route_id not in routes_dict:
            # Fetch route name
            cur.execute("SELECT route_name FROM trip WHERE route_id = ?", (route_id,))
            route_row = cur.fetchone()
            route_name = route_row['route_name'] if route_row else ""
            routes_dict[route_id] = {
                "route_id": route_id,
                "route_name": route_name,
                "trips": []
            }

        # Fetch all stops on this trip
        cur.execute("""
            SELECT stop_id, stop_sequence
            FROM stop_times
            WHERE trip_id = ?
            ORDER BY stop_sequence
        """, (trip_id,))
        stops_on_trip = [{"stop_id": s['stop_id'], "stop_sequence": s['stop_sequence']} for s in cur.fetchall()]

        # Determine index of current stop
        current_index = next((i for i, s in enumerate(stops_on_trip) if s['stop_id'] == stop_id), None)

        routes_dict[route_id]["trips"].append({
            "trip_id": trip_id,
            "current_stop_index": current_index,
            "stops_on_route": stops_on_trip
        })

    conn.close()
    return list(routes_dict.values())

print(get_routes_for_stop(379640)[0:2])