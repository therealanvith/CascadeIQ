from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import TypedDict

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
        with open(path, "rb") as f:
            artifact = pickle.load(f)
        if not isinstance(artifact, ModelArtifact):
            # Backward/forward safety: accept dict-like too.
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
            [
                [
                    float(req.speed_deviation),
                    float(req.weather_severity),
                    float(req.port_congestion),
                    float(req.distance_remaining),
                    float(req.month),
                ]
            ],
            dtype=np.float32,
        )
        prob = float(artifact.classifier.predict_proba(x)[0, 1])
        hours = float(max(0.0, artifact.regressor.predict(x)[0]))
        return {"delay_probability": prob, "estimated_delay_hours": hours}

