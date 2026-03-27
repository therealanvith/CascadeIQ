"""
MarineTraffic AIS data via the official HTTP API (not website scraping).

See: https://servicedocs.marinetraffic.com/ — authentication uses query `api_key`.

The URL shape matches the public Python client:
https://github.com/amphinicy/marine-traffic-client-api/blob/master/marinetrafficapi/bind.py
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def build_exportvessels_url(
    api_key: str,
    *,
    minlat: float,
    maxlat: float,
    minlon: float,
    maxlon: float,
    timespan_minutes: int = 60,
    protocol: str = "jsono",
    msgtype: str = "extended",
    version: str = "8",
) -> str:
    """
    PS02–PS06 family: `/exportvessels` with geographic filters.

    Area constraint from MarineTraffic docs:
    (MAXLAT - MINLAT) + (MAXLON - MINLON) <= 2
    """
    # Path: https://services.marinetraffic.com/api/exportvessels/{api_key}/{query segments...}
    base = f"https://services.marinetraffic.com/api/exportvessels/{api_key}"
    parts = [
        f"protocol:{protocol}",
        f"msgtype:{msgtype}",
        f"v:{version}",
        f"timespan:{int(timespan_minutes)}",
        f"MINLAT:{minlat}",
        f"MAXLAT:{maxlat}",
        f"MINLON:{minlon}",
        f"MAXLON:{maxlon}",
    ]
    return base + "/" + "/".join(parts)


def fetch_json(url: str, timeout_s: float = 45.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "CascadeIQ/1.0"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def fetch_exportvessels_bbox(
    *,
    minlat: float,
    maxlat: float,
    minlon: float,
    maxlon: float,
    timespan_minutes: int = 60,
    api_key: str | None = None,
) -> dict[str, Any]:
    key = (api_key or os.getenv("MARINETRAFFIC_API_KEY", "").strip()).strip()
    if not key:
        raise RuntimeError("MARINETRAFFIC_API_KEY is not set.")
    lat_span = abs(float(maxlat) - float(minlat))
    lon_span = abs(float(maxlon) - float(minlon))
    if lat_span + lon_span > 2.0001:
        raise ValueError(f"MarineTraffic area constraint violated: lat_span+lon_span={lat_span + lon_span} (must be <= 2).")

    url = build_exportvessels_url(
        key,
        minlat=minlat,
        maxlat=maxlat,
        minlon=minlon,
        maxlon=maxlon,
        timespan_minutes=timespan_minutes,
    )
    try:
        return fetch_json(url)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"MarineTraffic HTTP {e.code}: {body}") from e
