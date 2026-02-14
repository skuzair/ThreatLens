from shapely.geometry import Point, Polygon
from config import ZONES
import datetime

def get_zone(center):
    point = Point(center)

    for name, zone in ZONES.items():
        poly = Polygon(zone["polygon"])
        if poly.contains(point):
            return name, zone

    return None, None

def in_permitted_hours(timestamp, permitted_hours):
    hour = datetime.datetime.fromisoformat(timestamp).hour
    return permitted_hours[0] <= hour <= permitted_hours[1]
