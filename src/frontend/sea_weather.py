"""
Live sea conditions per district, from Open-Meteo (free, no API key).

- Marine API  -> waves, swell, sea surface temperature, ocean current, sea level
                 (sea_level_height_msl includes tides -> high/low tide times)
- Forecast API -> wind, gusts, rain, weather code (thunderstorms)

Each district is represented by ONE fixed point ~12-15 km offshore of its main
fishing harbour, since land readings say nothing about sea state.

These are weather-MODEL forecasts, not official warnings. Official fishermen
warnings come from INCOIS (ocean state / high-wave alerts) and IMD (weather);
the UI must always point users there.

Rating thresholds below are a first, conservative cut for small/medium boats
and should be tuned with local fishermen before real use.
"""

import requests

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEZONE = "Asia/Kolkata"
FORECAST_DAYS = 7

# Offshore point per district: (harbour the point is off, lat, lon)
DISTRICT_SEA_POINTS = {
    "TVPM": ("Vizhinjam", 8.38, 76.85),
    "KLM": ("Neendakara", 8.94, 76.40),
    "ALP": ("Alappuzha", 9.49, 76.18),
    "EKM": ("Kochi", 9.97, 76.10),
    "TCR": ("Chettuva", 10.52, 75.92),
    "MLPM": ("Ponnani", 10.78, 75.80),
    "KKD": ("Puthiyappa", 11.30, 75.64),
    "KNR": ("Azhikkal", 11.94, 75.18),
    "KSD": ("Kasaragod", 12.50, 74.86),
}

# (caution_at, rough_at) - reaching rough_at on ANY one measure makes it rough
WAVE_M = (1.5, 2.5)
WIND_KMH = (25, 40)
GUST_KMH = (35, 50)
THUNDERSTORM_CODES = {95, 96, 99}

CALM, CAUTION, ROUGH = "calm", "caution", "rough"

MARINE_VARS = ["wave_height", "wave_direction", "wave_period",
               "swell_wave_height", "swell_wave_direction", "swell_wave_period",
               "sea_surface_temperature", "ocean_current_velocity", "ocean_current_direction",
               "sea_level_height_msl"]
WEATHER_VARS = ["wind_speed_10m", "wind_gusts_10m", "wind_direction_10m",
                "precipitation", "weather_code"]


def _get(url, lat, lon, variables):
    params = {
        "latitude": lat, "longitude": lon, "timezone": TIMEZONE,
        "current": ",".join(variables), "hourly": ",".join(variables),
        "forecast_days": FORECAST_DAYS,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_sea_conditions(district_code):
    """Returns {"current": {...}, "hourly": [{time, ...}, ...], "harbour": str}.

    Raises requests.RequestException on network/API failure - caller decides
    how to show that.
    """
    harbour, lat, lon = DISTRICT_SEA_POINTS[district_code]
    marine = _get(MARINE_URL, lat, lon, MARINE_VARS)
    weather = _get(FORECAST_URL, lat, lon, WEATHER_VARS)

    current = {**marine["current"], **weather["current"]}

    # Both APIs return hourly series on the same local-time grid; join on time.
    weather_by_time = {
        t: {v: weather["hourly"][v][i] for v in WEATHER_VARS}
        for i, t in enumerate(weather["hourly"]["time"])
    }
    hourly = []
    for i, t in enumerate(marine["hourly"]["time"]):
        row = {"time": t, **{v: marine["hourly"][v][i] for v in MARINE_VARS}}
        row.update(weather_by_time.get(t, {}))
        hourly.append(row)

    return {"current": current, "hourly": hourly, "harbour": harbour}


def _level(value, thresholds):
    if value is None:
        return CALM
    caution_at, rough_at = thresholds
    if value >= rough_at:
        return ROUGH
    if value >= caution_at:
        return CAUTION
    return CALM


def rate_conditions(row):
    """Rates one reading (current or hourly row) as calm / caution / rough."""
    levels = [
        _level(row.get("wave_height"), WAVE_M),
        _level(row.get("wind_speed_10m"), WIND_KMH),
        _level(row.get("wind_gusts_10m"), GUST_KMH),
    ]
    if row.get("weather_code") in THUNDERSTORM_CODES:
        levels.append(ROUGH)
    if ROUGH in levels:
        return ROUGH
    if CAUTION in levels:
        return CAUTION
    return CALM


def tide_turns(hourly):
    """High and low tides as local maxima/minima of hourly sea level.

    Hourly data, so times are approximate (within ~30 min). Returns
    [{"time", "kind": "high"|"low", "level_m"}, ...].
    """
    levels = [(r["time"], r.get("sea_level_height_msl")) for r in hourly]
    turns = []
    for i in range(1, len(levels) - 1):
        (_, prev), (t, cur), (_, nxt) = levels[i - 1], levels[i], levels[i + 1]
        if None in (prev, cur, nxt):
            continue
        if cur > prev and cur >= nxt:
            turns.append({"time": t, "kind": "high", "level_m": cur})
        elif cur < prev and cur <= nxt:
            turns.append({"time": t, "kind": "low", "level_m": cur})
    return turns


def daily_summary(hourly):
    """Collapses hourly rows into one row per day using each day's worst values."""
    days = {}
    for row in hourly:
        days.setdefault(row["time"][:10], []).append(row)
    tides = tide_turns(hourly)

    def worst(rows, key):
        values = [r[key] for r in rows if r.get(key) is not None]
        return max(values) if values else None

    summary = []
    for date, rows in days.items():
        rain = [r["precipitation"] for r in rows if r.get("precipitation") is not None]
        worst_rating = max((rate_conditions(r) for r in rows), key=[CALM, CAUTION, ROUGH].index)
        # Direction/period reported at the hour of the biggest wave / strongest wind
        peak_wave = max(rows, key=lambda r: r.get("wave_height") or 0)
        peak_wind = max(rows, key=lambda r: r.get("wind_speed_10m") or 0)
        peak_current = max(rows, key=lambda r: r.get("ocean_current_velocity") or 0)
        summary.append({
            "date": date,
            "max_wave_height": worst(rows, "wave_height"),
            "wave_direction": peak_wave.get("wave_direction"),
            "wave_period": peak_wave.get("wave_period"),
            "max_swell_height": worst(rows, "swell_wave_height"),
            "max_wind_speed": worst(rows, "wind_speed_10m"),
            "wind_direction": peak_wind.get("wind_direction_10m"),
            "max_wind_gusts": worst(rows, "wind_gusts_10m"),
            "max_current": peak_current.get("ocean_current_velocity"),
            "current_direction": peak_current.get("ocean_current_direction"),
            "high_tides": [x["time"][11:16] for x in tides if x["time"][:10] == date and x["kind"] == "high"],
            "low_tides": [x["time"][11:16] for x in tides if x["time"][:10] == date and x["kind"] == "low"],
            "total_rain_mm": sum(rain) if rain else None,
            "thunderstorm": any(r.get("weather_code") in THUNDERSTORM_CODES for r in rows),
            "rating": worst_rating,
        })
    return summary


def sky_kind(weather_code, is_day=1):
    """Groups a WMO weather code into the sky picture shown on the map."""
    if weather_code is None:
        return None
    if weather_code in THUNDERSTORM_CODES:
        return "storm"
    if weather_code >= 61:  # rain, showers (snow codes never occur on this coast)
        return "rain"
    if weather_code >= 51:
        return "drizzle"
    if weather_code in (45, 48):
        return "fog"
    if weather_code == 3:
        return "cloudy"
    if weather_code in (1, 2):
        return "partly" if is_day else "partly_night"
    return "clear" if is_day else "clear_night"


def compass(degrees):
    if degrees is None:
        return "-"
    points = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return points[round(degrees / 45) % 8]
