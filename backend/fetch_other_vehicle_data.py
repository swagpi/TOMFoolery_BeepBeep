import csv
import requests
from io import StringIO
import sqlite3
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


DB_PATH = "tomfoolery-rs-main/database.db"

def parse_timestamp(ts: str):
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)  # assumes string like "2025-11-28T14:55:00"
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
        return dt
    except Exception:
        return None


def download_vehicle_data(url: str="https://api.mobidata-bw.de/geoserver/MobiData-BW/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=MobiData-BW%3Asharing_vehicles&maxFeatures=100000&outputFormat=csv"):
    """
    loads other vehicle data like scooters and car sharing
    :param url: url of data to be fetched
    :return:
    """
    response = requests.get(url)
    response.raise_for_status()
    f = StringIO(response.text)
    reader = csv.DictReader(f)


    vehicles = []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=90)


    for row in reader:

        ts = parse_timestamp(row.get("last_reported"))
        if ts is None or ts < cutoff:
            continue


        g = row["geometry"]
        lon_str, lat_str = g[7:-1].split(" ")
        lon = float(lon_str)
        lat = float(lat_str)

        vehicles.append([
            row["vehicle_id"],
            row["form_factor"],
            lat,
            lon,
            row.get("current_range_meters"),
            row.get("last_reported"),
            row.get("rental_uris_web"),
        ])
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS other_vehicles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                vehicle_id TEXT NOT NULL,
                form_factor TEXT,

                lat REAL,
                lon REAL,

                current_range_meters INTEGER,
                last_reported TEXT,
                rental_uris_web TEXT
                )
        """)

    cur.execute("DELETE FROM other_vehicles")
    cur.executemany("""
        INSERT INTO other_vehicles (
            vehicle_id, form_factor, lat, lon,
            current_range_meters, last_reported, rental_uris_web
        ) VALUES (?,?,?,?,?,?,?)
    """, vehicles)

    con.commit()
    con.close()


download_vehicle_data()


