from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import TypedDict
import joblib
import numpy as np

from model.schema import PredictRequest
from model.train import ModelArtifact, ensure_model_artifact



class PredictResult(TypedDict):
    delay_probability: float
    estimated_delay_hours: float


def _artifact_path() -> Path:
    env = os.getenv("MODEL_PATH", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent / "vessel_delay_model.pkl"


class DelayModelBundle:
    _cached: ModelArtifact | None = None

    @classmethod
    def load(cls) -> ModelArtifact:
        if cls._cached is not None:
            return cls._cached
        ensure_model_artifact()
        path = _artifact_path()
        import model.train as _train_module  # ensure ModelArtifact is registered
        import sys
        sys.modules['__main__'].ModelArtifact = ModelArtifact  # patch for pickle
        artifact = joblib.load(path)
        if not isinstance(artifact, ModelArtifact):
            artifact = ModelArtifact(
                classifier=artifact["classifier"],
                regressor=artifact["regressor"],
                feature_order=artifact["feature_order"],
            )
        cls._cached = artifact
        return artifact

    @classmethod
    def predict(cls, req: PredictRequest) -> PredictResult:
        artifact = cls.load()
        x = np.array(
            [[
                float(req.speed_deviation),
                float(req.weather_severity),
                float(req.port_congestion),
                float(req.distance_remaining),
                float(req.month),
            ]],
            dtype=np.float32,
        )
        hours = float(max(0.0, artifact.regressor.predict(x)[0]))
        # Derive probability from predicted hours — consistent by design
        prob = float(min(1.0, hours / max(artifact.max_delay, 1.0)))
        return {"delay_probability": prob, "estimated_delay_hours": hours}