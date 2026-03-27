from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from model.schema import PredictRequest

RiskLevel = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class DemoVessel:
    vessel_id: str
    name: str
    route_name: str
    origin: str
    destination: str
    status: str
    lat: float
    lon: float
    # Features for prediction
    features: PredictRequest


DEMO_VESSELS: list[DemoVessel] = [
    DemoVessel(
        vessel_id="vessel:endeavour",
        name="MV Endeavour",
        route_name="Mumbai-Singapore",
        origin="Mumbai",
        destination="Singapore",
        status="delayed",
        lat=16.8,
        lon=73.0,
        features=PredictRequest(
            speed_deviation=-14.2,
            weather_severity=7.8,
            port_congestion=7.2,
            distance_remaining=980.0,
            month=3,
        ),
    ),
    DemoVessel(
        vessel_id="vessel:atlantic_star",
        name="MV Atlantic Star",
        route_name="Chennai-Dubai",
        origin="Chennai",
        destination="Dubai",
        status="on_schedule",
        lat=13.2,
        lon=80.6,
        features=PredictRequest(
            speed_deviation=-1.4,
            weather_severity=2.0,
            port_congestion=3.1,
            distance_remaining=1450.0,
            month=3,
        ),
    ),
    DemoVessel(
        vessel_id="vessel:pacific_dawn",
        name="MV Pacific Dawn",
        route_name="Kolkata-Rotterdam",
        origin="Kolkata",
        destination="Rotterdam",
        status="slight_delay",
        lat=19.7,
        lon=86.8,
        features=PredictRequest(
            speed_deviation=-6.0,
            weather_severity=4.8,
            port_congestion=5.9,
            distance_remaining=7100.0,
            month=3,
        ),
    ),
]


def _risk_level(prob: float) -> RiskLevel:
    if prob >= 0.67:
        return "high"
    if prob >= 0.34:
        return "medium"
    return "low"


def _route_polyline(route_name: str) -> list[dict[str, float]]:
    # Very lightweight mock polylines (lat/lon) for map rendering.
    if route_name == "Mumbai-Singapore":
        return [
            {"lat": 19.076, "lon": 72.8777},
            {"lat": 10.0, "lon": 78.0},
            {"lat": 1.3521, "lon": 103.8198},
        ]
    if route_name == "Chennai-Dubai":
        return [
            {"lat": 13.0827, "lon": 80.2707},
            {"lat": 10.0, "lon": 75.0},
            {"lat": 25.2048, "lon": 55.2708},
        ]
    if route_name == "Kolkata-Rotterdam":
        return [
            {"lat": 22.5726, "lon": 88.3639},
            {"lat": 10.0, "lon": 80.0},
            {"lat": 35.0, "lon": 20.0},
            {"lat": 51.9244, "lon": 4.4777},
        ]
    # Mumbai-Rotterdam
    return [
        {"lat": 19.076, "lon": 72.8777},
        {"lat": 15.0, "lon": 60.0},
        {"lat": 35.0, "lon": 20.0},
        {"lat": 51.9244, "lon": 4.4777},
    ]


def list_vessels_with_risk(model: Any, vessels: list[DemoVessel]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for v in vessels:
        pred = model.predict(v.features)
        prob = float(pred["delay_probability"])
        hours = float(pred["estimated_delay_hours"])
        out.append(
            {
                "vessel_id": v.vessel_id,
                "name": v.name,
                "route": v.route_name,
                "origin": v.origin,
                "destination": v.destination,
                "status": v.status,
                "position": {"lat": v.lat, "lon": v.lon},
                "route_polyline": _route_polyline(v.route_name),
                "risk": {
                    "delay_probability": round(prob, 3),
                    "estimated_delay_hours": round(hours, 2),
                    "risk_level": _risk_level(prob),
                },
                "features": v.features.model_dump(),
            }
        )
    return out

