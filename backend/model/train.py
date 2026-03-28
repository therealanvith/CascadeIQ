from __future__ import annotations

import os
import pickle
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from xgboost import XGBRegressor

from data.real_ais_training import load_training_dataframe

load_dotenv()
from model.features import FEATURE_ORDER


@dataclass(frozen=True)
class ModelArtifact:
    regressor: XGBRegressor
    feature_order: list[str]
    max_delay: float  # used to normalize probability


def _artifact_path() -> Path:
    env = os.getenv("MODEL_PATH", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent / "vessel_delay_model.pkl"


def train_and_save(seed: int = 42) -> Path:
    df = load_training_dataframe()
    if len(df) < 50:
        raise RuntimeError(
            f"Not enough training rows (need >= 50, got {len(df)})."
        )

    X = df[FEATURE_ORDER].to_numpy(dtype=np.float32)
    y_hours = df["delay_hours"].to_numpy(dtype=np.float32)

    reg = XGBRegressor(
        n_estimators=400,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=2.0,
        min_child_weight=5,
        objective="reg:squarederror",
        random_state=seed,
        n_jobs=2,
    )
    reg.fit(X, y_hours)

    max_delay = float(np.percentile(y_hours, 95))

    artifact = ModelArtifact(
        regressor=reg,
        feature_order=list(FEATURE_ORDER),
        max_delay=max_delay,
    )
    path = _artifact_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, path)
    return path


def ensure_model_artifact() -> Path:
    path = _artifact_path()
    if path.exists():
        return path
    return train_and_save()


if __name__ == "__main__":
    p = train_and_save()
    print(f"Saved model to {p}")