"""
Build an ML training table from **real AIS** data.

Primary source: MarineTraffic official API (`exportvessels` in a bounded area).
We do **not** scrape the MarineTraffic website HTML map URL — use an API key per their terms.

Labels:
- `delay_hours` is derived from AIS voyage fields when available:
  `max(0, ETA - ETA_CALC)` in hours (ship-reported ETA vs MarineTraffic calculated ETA).
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from data.marinetraffic_client import fetch_exportvessels_bbox
from data.open_meteo import weather_severity_from_wind_ms, wind_speed_ms
from model.features import FEATURE_ORDER


def _parse_dt(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    s = str(val).strip()
    if not s or s.upper() in {"NULL", "NONE", ""}:
        return None
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(s[:19], fmt)
            except ValueError:
                continue
    return None


def _as_float(x: Any) -> float | None:
    try:
        if x is None:
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def _as_int(x: Any) -> int | None:
    try:
        if x is None:
            return None
        return int(float(x))
    except (TypeError, ValueError):
        return None


def _extract_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """
    MarineTraffic JSON responses are typically: {"DATA": [ {...}, ... ], "METADATA": ...}
    Some legacy shapes may differ — handle defensively.
    """
    if not isinstance(payload, dict):
        return []
    if "errors" in payload:
        errs = payload.get("errors") or []
        raise RuntimeError(f"MarineTraffic API error payload: {errs}")
    data = payload.get("DATA")
    if data is None:
        # Some responses might nest differently
        data = payload.get("data")
    if data is None:
        return []
    if isinstance(data, dict):
        # Rare: single object
        return [data]
    if isinstance(data, list):
        out: list[dict[str, Any]] = []
        for item in data:
            if isinstance(item, dict):
                out.append(item)
        return out
    return []


def _speed_knots_from_row(row: dict[str, Any]) -> float | None:
    # MarineTraffic: SPEED is often knots * 10 (integer)
    sp = _as_int(row.get("SPEED"))
    if sp is None:
        spf = _as_float(row.get("SPEED"))
        if spf is None:
            return None
        return float(spf) / 10.0 if abs(spf) > 40 else float(spf)
    return float(sp) / 10.0


def _delay_hours_label(row: dict[str, Any]) -> float | None:
    eta = _parse_dt(row.get("ETA"))
    eta_calc = _parse_dt(row.get("ETA_CALC"))
    if eta is None or eta_calc is None:
        return None
    dh = (eta - eta_calc).total_seconds() / 3600.0
    # If ship ETA is earlier than model ETA, treat as "no extra delay"
    return float(max(0.0, dh))


def _month_from_row(row: dict[str, Any]) -> int | None:
    ts = _parse_dt(row.get("TIMESTAMP"))
    if ts is None:
        return None
    return int(ts.month)


def _tiles_around_center(
    center_lat: float,
    center_lon: float,
    *,
    lat_span: float = 1.0,
    lon_span: float = 1.0,
    rings: int = 2,
) -> list[tuple[float, float, float, float]]:
    """
    Build non-overlapping-ish bbox tiles that satisfy (Δlat + Δlon) <= 2.
    Using equal spans: lat_span + lon_span must be <= 2.
    """
    if lat_span + lon_span > 2.0001:
        raise ValueError("lat_span + lon_span must be <= 2 for MarineTraffic area queries.")

    tiles: list[tuple[float, float, float, float]] = []
    step_lat = lat_span
    step_lon = lon_span
    for dy in range(-rings, rings + 1):
        for dx in range(-rings, rings + 1):
            c_lat = center_lat + dy * step_lat
            c_lon = center_lon + dx * step_lon
            minlat = c_lat - lat_span / 2.0
            maxlat = c_lat + lat_span / 2.0
            minlon = c_lon - lon_span / 2.0
            maxlon = c_lon + lon_span / 2.0
            tiles.append((minlat, maxlat, minlon, maxlon))
    return tiles


def fetch_marinetraffic_training_rows(
    *,
    center_lat: float | None = None,
    center_lon: float | None = None,
    timespan_minutes: int = 60,
    sleep_s: float = 0.35,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Fetch multiple tiles around the map center (defaults match the hackathon link viewport center).
    Returns a dataframe of engineered features + raw rows for debugging.
    """
    clat = float(center_lat if center_lat is not None else os.getenv("MARINETRAFFIC_CENTER_LAT", "14.7"))
    clon = float(center_lon if center_lon is not None else os.getenv("MARINETRAFFIC_CENTER_LON", "74.9"))
    rings = int(os.getenv("MARINETRAFFIC_RING_COUNT", "2"))
    rings = max(1, min(5, rings))

    tiles = _tiles_around_center(clat, clon, lat_span=1.0, lon_span=1.0, rings=rings)
    all_rows: list[dict[str, Any]] = []
    for minlat, maxlat, minlon, maxlon in tiles:
        payload = fetch_exportvessels_bbox(
            minlat=minlat,
            maxlat=maxlat,
            minlon=minlon,
            maxlon=maxlon,
            timespan_minutes=timespan_minutes,
        )
        part = _extract_rows(payload)
        # Tag with tile for congestion proxy
        for r in part:
            r["_tile_id"] = f"{minlat:.3f},{minlon:.3f}"
        all_rows.extend(part)
        time.sleep(sleep_s)

    if not all_rows:
        raise RuntimeError("MarineTraffic returned no vessel rows — check API credits, filters, or bbox coverage.")

    # Congestion proxy uses per-tile counts before de-duplication
    tile_counts: dict[str, int] = {}
    for r in all_rows:
        tid = str(r.get("_tile_id") or "unknown")
        tile_counts[tid] = tile_counts.get(tid, 0) + 1

    # De-dupe by MMSI (prefer latest TIMESTAMP)
    df_raw = pd.DataFrame(all_rows)
    if "MMSI" in df_raw.columns and "TIMESTAMP" in df_raw.columns:
        df_raw = df_raw.sort_values(by=["MMSI", "TIMESTAMP"], ascending=[True, True])
        df_raw = df_raw.drop_duplicates(subset=["MMSI"], keep="last")

    rows = df_raw.to_dict(orient="records")

    # Weather cache by rounded coordinate
    weather_cache: dict[tuple[str, str], float | None] = {}

    def get_ws(lat: float, lon: float) -> float | None:
        key = (f"{lat:.1f}", f"{lon:.1f}")
        if key in weather_cache:
            return weather_cache[key]
        ws = wind_speed_ms(key[0], key[1])
        weather_cache[key] = ws
        return ws

    engineered: list[dict[str, Any]] = []
    for r in rows:
        lat = _as_float(r.get("LAT"))
        lon = _as_float(r.get("LON"))
        if lat is None or lon is None:
            continue

        speed_kn = _speed_knots_from_row(r)
        avg_kn = _as_float(r.get("AVG_SPEED"))
        if speed_kn is None or avg_kn is None or avg_kn <= 0.1:
            continue

        delay_hours = _delay_hours_label(r)
        if delay_hours is None:
            continue

        speed_deviation = float((speed_kn - avg_kn) / max(avg_kn, 0.1) * 100.0)
        dist = _as_float(r.get("DISTANCE_TO_GO"))
        if dist is None:
            continue

        month = _month_from_row(r)
        if month is None:
            continue

        ws = get_ws(lat, lon)
        weather_severity = weather_severity_from_wind_ms(ws)

        tid = str(r.get("_tile_id") or "unknown")
        n_tile = max(1, int(tile_counts.get(tid, 1)))
        # More vessels in the same AOI snapshot ~ more congestion pressure (proxy feature)
        port_congestion = float(min(10.0, (n_tile / 25.0) * 10.0))

        engineered.append(
            {
                "speed_deviation": float(np.clip([speed_deviation], -40.0, 40.0)[0]),
                "weather_severity": float(np.clip([weather_severity], 0.0, 10.0)[0]),
                "port_congestion": float(np.clip([port_congestion], 0.0, 10.0)[0]),
                "distance_remaining": float(max(0.0, dist)),
                "month": int(month),
                "delay_hours": float(max(0.0, delay_hours)),
            }
        )

    out = pd.DataFrame(engineered)
    if out.empty:
        raise RuntimeError(
            "Could not engineer any training rows from MarineTraffic data. "
            "This usually means ETA/ETA_CALC fields were missing for vessels in the sampled area."
        )
    return out, rows


def load_training_dataframe_from_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = set(FEATURE_ORDER) | {"delay_hours"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Training CSV missing columns: {sorted(missing)}")
    cols = list(FEATURE_ORDER) + ["delay_hours"]
    return df[cols].copy()


def load_training_dataframe() -> pd.DataFrame:
    """
    Priority:
    1) AIS_TRAINING_CSV (explicit dataset path)
    2) Fetch from MarineTraffic API using MARINETRAFFIC_API_KEY
    """
    csv_path = os.getenv("AIS_TRAINING_CSV", "").strip()
    if csv_path:
        return load_training_dataframe_from_csv(csv_path)

    if not os.getenv("MARINETRAFFIC_API_KEY", "").strip():
        raise RuntimeError(
            "Real-data training requires MARINETRAFFIC_API_KEY (official MarineTraffic API) "
            "or AIS_TRAINING_CSV with columns: "
            "speed_deviation, weather_severity, port_congestion, distance_remaining, month, delay_hours. "
            "Scraping the MarineTraffic website is not supported."
        )

    df, _raw = fetch_marinetraffic_training_rows()
    return df
