"""
Potential Fishing Zones (PFZ) near a district's harbour, from INCOIS.

INCOIS publishes daily PFZ advisories: lines at sea where fish are likely to
gather, worked out from satellite sea-surface temperature and chlorophyll. They
are NOT per species - they point to shoaling pelagic fish in general (sardine,
mackerel etc.). We show them unchanged and only add, per zone:
- distance and direction from the district's harbour (as INCOIS text advisories do)
- current sea conditions AT the zone (Open-Meteo), rated calm / caution / rough

Source: the public WFS layer behind INCOIS's own PFZ WebGIS map
(incois.gov.in/MarineFisheries/PfzWebGis). INCOIS does not issue zones on
cloudy days or during the fishing ban, so "no zones" is a normal answer.
"""

import math
from datetime import date, timedelta

import requests

from sea_weather import FORECAST_URL, MARINE_URL, TIMEZONE, rate_conditions

PFZ_WFS_URL = "https://incois.gov.in/geoserver/PFZ_Automation/ows"

# Main fishing harbour per district (lat, lon) - the "from" point for directions.
DISTRICT_HARBOURS = {
    "TVPM": ("Vizhinjam", 8.379, 76.996),
    "KLM": ("Neendakara", 8.938, 76.540),
    "ALP": ("Alappuzha", 9.493, 76.317),
    "EKM": ("Kochi", 9.945, 76.255),
    "TCR": ("Chettuva", 10.533, 76.045),
    "MLPM": ("Ponnani", 10.777, 75.918),
    "KKD": ("Puthiyappa", 11.317, 75.750),
    "KNR": ("Azhikkal", 11.943, 75.305),
    "KSD": ("Kasaragod", 12.497, 74.985),
}
MAX_ZONE_KM = 100  # zones further than this from the harbour are not listed


def fetch_kerala_pfz():
    """Returns {"date": date | None, "zones": [{"uid", "path": [[lon, lat], ...]}, ...]}."""
    params = {
        "service": "WFS", "version": "1.1.0", "request": "GetFeature",
        "typeName": "PFZ_Automation:pfzlines", "outputFormat": "application/json",
        "CQL_FILTER": "State_Name='KERALA'",
    }
    resp = requests.get(PFZ_WFS_URL, params=params, timeout=40,
                        headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    features = resp.json().get("features", [])

    zones, advisory_date = [], None
    for f in features:
        props = f["properties"]
        if advisory_date is None and props.get("Year") and props.get("Julian_day"):
            advisory_date = date(int(props["Year"]), 1, 1) + timedelta(days=int(props["Julian_day"]) - 1)
        geom = f["geometry"]
        lines = geom["coordinates"] if geom["type"] == "MultiLineString" else [geom["coordinates"]]
        for line in lines:
            zones.append({"uid": props.get("UID"), "path": [[p[0], p[1]] for p in line]})
    return {"date": advisory_date, "zones": zones}


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _bearing(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def _destination(lat, lon, bearing, km):
    r = 6371.0
    p1, l1, b = math.radians(lat), math.radians(lon), math.radians(bearing)
    d = km / r
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p1), math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), math.degrees(l2)


OFFSHORE_KM = (10, 25, 50)
OFFSHORE_BEARING = 250  # straight out to sea: the Kerala coast faces west-south-west


def offshore_points(district_code, kms=OFFSHORE_KM):
    """Sample points straight out to sea from the district harbour, used to show
    the weather at sea when there is no fishing zone advisory."""
    _, h_lat, h_lon = DISTRICT_HARBOURS[district_code]
    return [{"km": km, "point": _destination(h_lat, h_lon, OFFSHORE_BEARING, km)} for km in kms]


def zones_near_district(pfz, district_code, max_km=MAX_ZONE_KM):
    """Zones within max_km of the district harbour, nearest first, each with
    nearest-point distance/bearing and the midpoint used for sea conditions."""
    _, h_lat, h_lon = DISTRICT_HARBOURS[district_code]
    result = []
    for z in pfz["zones"]:
        lon, lat = min(z["path"], key=lambda p: _haversine_km(h_lat, h_lon, p[1], p[0]))
        km = _haversine_km(h_lat, h_lon, lat, lon)
        if km > max_km:
            continue
        mid_lon, mid_lat = z["path"][len(z["path"]) // 2]
        result.append({
            **z,
            "nearest_km": km,
            "bearing": _bearing(h_lat, h_lon, lat, lon),
            "nearest_point": (lat, lon),
            "mid": (mid_lat, mid_lon),
        })
    return sorted(result, key=lambda z: z["nearest_km"])


def zone_conditions(points):
    """Current sea state at several (lat, lon) points in one request per API.
    Returns a list of current-reading dicts in the same order, each with "rating"."""
    if not points:
        return []
    lats = ",".join(f"{p[0]:.4f}" for p in points)
    lons = ",".join(f"{p[1]:.4f}" for p in points)

    def get(url, variables):
        resp = requests.get(url, timeout=15, params={
            "latitude": lats, "longitude": lons, "timezone": TIMEZONE, "current": variables})
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else [data]

    marine = get(MARINE_URL, "wave_height")
    weather = get(FORECAST_URL, "wind_speed_10m,wind_gusts_10m,weather_code,cloud_cover,is_day")
    readings = []
    for m, w in zip(marine, weather):
        reading = {**m.get("current", {}), **w.get("current", {})}
        reading["rating"] = rate_conditions(reading)
        readings.append(reading)
    return readings
