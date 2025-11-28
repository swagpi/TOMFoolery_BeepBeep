import requests
from google.transit import gtfs_realtime_pb2

def download_rt_gtfs_data(url: str="https://realtime.gtfs.de/realtime-free.pb"):
    """
    fetches real-time gtfs updates from url
    :param url: the url of datastream
    :return: [[vehicles], [trip_updates], [alerts]]
    """
    raw = requests.get(url).content

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(raw)

    vehicles = []

    for entity in feed.entity:
        if entity.HasField("vehicle"):
            v = entity.vehicle

            vehicles.append({
                "trip_id": v.trip.trip_id,
                "route_id": v.trip.route_id,
                "lat": v.position.latitude,
                "lon": v.position.longitude,
                "bearing": v.position.bearing,
                "speed": v.position.speed,
                "timestamp": v.timestamp,
                "vehicle_id": v.vehicle.id
            })

    trip_updates = []

    for entity in feed.entity:
        if entity.HasField("trip_update"):
            tu = entity.trip_update
            for stu in tu.stop_time_update:
                trip_updates.append({
                    "trip_id": tu.trip.trip_id,
                    "stop_id": stu.stop_id,
                    "arrival_delay": stu.arrival.delay if stu.HasField("arrival") else None,
                    "departure_delay": stu.departure.delay if stu.HasField("departure") else None,
                })

    alerts = []

    for entity in feed.entity:
        if entity.HasField("alert"):
            a = entity.alert
            alerts.append({
                "header": a.header_text.translation[0].text if a.header_text.translation else None,
                "description": a.description_text.translation[0].text if a.description_text.translation else None,
                "cause": a.cause,
                "effect": a.effect,
            })

    print(len(vehicles), "\n", len(trip_updates), "\n", len(alerts), "\n")
    print(trip_updates[:10])

    # Apparently no vehicle positions in german data

    return [vehicles, trip_updates, alerts]

