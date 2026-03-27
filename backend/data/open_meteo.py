"""Free weather (no API key) for feature engineering — Open-Meteo."""

from __future__ import annotations

import json
import urllib.request
from functools import lru_cache


@lru_cache(maxsize=512)
def wind_speed_ms(lat_rounded: str, lon_rounded: str) -> float | None:
    """
    Current wind speed at ~0.1° resolution (rounded by caller).
    Returns None if request fails.
    """
    lat = float(lat_rounded)
    lon = float(lon_rounded)
    q = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
        }
    )
    url = f"https://api.open-meteo.com/v1/forecast?{q}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CascadeIQ/1.0"})
        with urllib.request.urlopen(req, timeout=20.0) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        cw = data.get("current_weather") or {}
        ws = cw.get("windspeed")
        if ws is None:
            cur = data.get("current") or {}
            ws = cur.get("wind_speed_10m")
        if ws is None:
            return None
        return float(ws)
    except Exception:
        return None


def weather_severity_from_wind_ms(wind_ms: float | None) -> float:
    if wind_ms is None:
        return 0.0
    # Map typical winds into 0–10 (rough, for ML features only)
    return float(min(10.0, max(0.0, (wind_ms / 18.0) * 10.0)))
