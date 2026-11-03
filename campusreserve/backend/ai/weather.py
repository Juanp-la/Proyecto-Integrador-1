"""
Weather data from Open-Meteo (https://open-meteo.com) — free, no API key.

The AI does NOT know the real-time weather by itself, so we fetch the real
hourly forecast here and then (in services.py) ask the AI to turn it into a
readable daily report. Bad-weather detection is a deterministic rule, so
alerts don't depend on the AI being available.
"""

import json
import logging
import urllib.parse
import urllib.request
from datetime import date, time, timedelta

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_KEY = "ai:weather:forecast"
CACHE_SECONDS = 30 * 60

# WMO weather codes -> Spanish description + emoji
WEATHER_CODES = {
    0: ("Despejado", "☀️"),
    1: ("Mayormente despejado", "🌤️"),
    2: ("Parcialmente nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Niebla", "🌫️"),
    48: ("Niebla con escarcha", "🌫️"),
    51: ("Llovizna ligera", "🌦️"),
    53: ("Llovizna", "🌦️"),
    55: ("Llovizna fuerte", "🌧️"),
    56: ("Llovizna helada", "🌧️"),
    57: ("Llovizna helada fuerte", "🌧️"),
    61: ("Lluvia ligera", "🌦️"),
    63: ("Lluvia", "🌧️"),
    65: ("Lluvia fuerte", "🌧️"),
    66: ("Lluvia helada", "🌧️"),
    67: ("Lluvia helada fuerte", "🌧️"),
    71: ("Nieve ligera", "🌨️"),
    73: ("Nieve", "🌨️"),
    75: ("Nieve fuerte", "🌨️"),
    77: ("Granizo fino", "🌨️"),
    80: ("Chubascos ligeros", "🌦️"),
    81: ("Chubascos", "🌧️"),
    82: ("Chubascos fuertes", "⛈️"),
    85: ("Chubascos de nieve", "🌨️"),
    86: ("Chubascos de nieve fuertes", "🌨️"),
    95: ("Tormenta eléctrica", "⛈️"),
    96: ("Tormenta con granizo", "⛈️"),
    99: ("Tormenta fuerte con granizo", "⛈️"),
}

HEAVY_CODES = {55, 57, 65, 67, 75, 82, 86}
THUNDER_CODES = {95, 96, 99}


def describe(code):
    return WEATHER_CODES.get(code, ("Desconocido", "🌡️"))


def fetch_forecast():
    """
    Returns {"hourly": {"YYYY-MM-DDTHH:00": {...}}, "daily": {"YYYY-MM-DD": {...}}}
    or None if Open-Meteo can't be reached. Cached for 30 minutes.
    """
    cached = cache.get(CACHE_KEY)
    if cached:
        return cached

    params = {
        "latitude": settings.CAMPUS_LATITUDE,
        "longitude": settings.CAMPUS_LONGITUDE,
        "timezone": settings.TIME_ZONE,
        "forecast_days": 7,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,is_day,wind_speed_10m",
        "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
    }
    url = OPEN_METEO_URL + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=8) as res:
            raw = json.loads(res.read().decode("utf-8"))
    except Exception as exc:  # network down, timeout, bad JSON...
        logger.warning("Open-Meteo request failed: %s", exc)
        return None

    forecast = parse_open_meteo(raw)
    cache.set(CACHE_KEY, forecast, CACHE_SECONDS)
    return forecast


def parse_open_meteo(raw):
    h = raw.get("hourly", {})
    hourly = {}
    for i, ts in enumerate(h.get("time", [])):
        hourly[ts] = {
            "temperature": h["temperature_2m"][i],
            "precipitation_probability": h["precipitation_probability"][i] or 0,
            "precipitation": h["precipitation"][i] or 0,
            "weather_code": h["weather_code"][i],
            "wind_speed": h["wind_speed_10m"][i],
        }
    d = raw.get("daily", {})
    daily = {}
    for i, day in enumerate(d.get("time", [])):
        daily[day] = {
            "weather_code": d["weather_code"][i],
            "temp_max": d["temperature_2m_max"][i],
            "temp_min": d["temperature_2m_min"][i],
            "precipitation_sum": d["precipitation_sum"][i] or 0,
            "precipitation_probability_max": d["precipitation_probability_max"][i] or 0,
        }
    c = raw.get("current") or {}
    current = None
    if c:
        current = {
            "time": c.get("time"),
            "temperature": c.get("temperature_2m"),
            "apparent_temperature": c.get("apparent_temperature"),
            "humidity": c.get("relative_humidity_2m"),
            "precipitation": c.get("precipitation") or 0,
            "weather_code": c.get("weather_code"),
            "is_day": c.get("is_day"),
            "wind_speed": c.get("wind_speed_10m"),
        }
    return {"hourly": hourly, "daily": daily, "current": current}


def hours_for(forecast, day: date, start: time, end: time):
    """
    One entry per hour window inside [start, end) on `day`.

    Open-Meteo reports precipitation and rain probability for the PRECEDING
    hour: the value stamped "18:00" is the rain between 17:00 and 18:00. So the
    window 17:00-18:00 reads the "18:00" entry. Each returned entry is labelled
    with the start of its window ("hour": "17:00").
    """
    if not forecast:
        return []
    result = []
    first = start.hour
    last = end.hour if end.minute == 0 else end.hour + 1  # exclusive
    for window_start in range(first, last):
        key = f"{day.isoformat()}T{window_start + 1:02d}:00"
        if window_start + 1 == 24:
            key = f"{(day + timedelta(days=1)).isoformat()}T00:00"
        if key in forecast["hourly"]:
            result.append({"hour": f"{window_start:02d}:00", **forecast["hourly"][key]})
    return result


def is_bad_hour(h) -> bool:
    """Rule used for alerts: storm, heavy rain, or very likely rain."""
    return (
        h["weather_code"] in THUNDER_CODES
        or h["weather_code"] in HEAVY_CODES
        or h["precipitation"] >= settings.WEATHER_BAD_PRECIPITATION_MM
        or h["precipitation_probability"] >= settings.WEATHER_BAD_PROBABILITY
    )


def bad_weather_summary(hours):
    """Returns a dict describing the worst hour if any hour is bad, else None."""
    bad = [h for h in hours if is_bad_hour(h)]
    if not bad:
        return None
    worst = max(bad, key=lambda h: (h["weather_code"] in THUNDER_CODES, h["precipitation_probability"], h["precipitation"]))
    label, icon = describe(worst["weather_code"])
    return {
        "label": label,
        "icon": icon,
        "hour": worst["hour"],
        "precipitation_probability": worst["precipitation_probability"],
        "precipitation": worst["precipitation"],
        "temperature": worst["temperature"],
    }
