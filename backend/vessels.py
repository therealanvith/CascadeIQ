from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from model.schema import PredictRequest
import searoute as sr

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
    routes = {
        "Mumbai-Singapore": ([72.877, 19.076], [103.819, 1.352]),
        "Chennai-Dubai": ([80.270, 13.082], [55.270, 25.204]),
        "Kolkata-Rotterdam": ([88.363, 22.572], [4.477, 51.924]),
    }
    if route_name not in routes:
        return []
    origin, destination = routes[route_name]
    try:
        route = sr.searoute(origin, destination)
        return [
            {"lat": coord[1], "lon": coord[0]}
            for coord in route["geometry"]["coordinates"]
        ]
    except Exception:
        return [
            {"lat": origin[1], "lon": origin[0]},
            {"lat": destination[1], "lon": destination[0]},
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

