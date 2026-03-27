from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    speed_deviation: float = Field(..., description="Percent deviation from expected speed, e.g. -15 to +15")
    weather_severity: float = Field(..., ge=0, le=10, description="0-10 severity")
    port_congestion: float = Field(..., ge=0, le=10, description="0-10 congestion")
    distance_remaining: float = Field(..., ge=0, description="Remaining distance (nautical miles-ish scale)")
    month: int = Field(..., ge=1, le=12)

