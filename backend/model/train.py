from __future__ import annotations

import os
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from xgboost import XGBClassifier, XGBRegressor

from backend.data.real_ais_training import load_training_dataframe

load_dotenv()
from backend.model.features import FEATURE_ORDER


@dataclass(frozen=True)
class ModelArtifact:
    classifier: XGBClassifier
    regressor: XGBRegressor
    feature_order: list[str]


def _artifact_path() -> Path:
    env = os.getenv("MODEL_PATH", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent / "vessel_delay_model.pkl"


def train_and_save(seed: int = 42) -> Path:
    df = load_training_dataframe()
    if len(df) < 50:
        raise RuntimeError(
            f"Not enough real training rows (need >= 50, got {len(df)}). "
            "Try widening the MarineTraffic tile grid, increasing timespan, or providing AIS_TRAINING_CSV."
        )

    X = df[FEATURE_ORDER].to_numpy(dtype=np.float32)
    y_hours = df["delay_hours"].to_numpy(dtype=np.float32)
    y_delayed = (y_hours > 1.0).astype(np.int32)

    clf = XGBClassifier(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=seed,
        n_jobs=2,
    )
    reg = XGBRegressor(
        n_estimators=350,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        objective="reg:squarederror",
        random_state=seed,
        n_jobs=2,
    )

    clf.fit(X, y_delayed)
    reg.fit(X, y_hours)

    artifact = ModelArtifact(classifier=clf, regressor=reg, feature_order=list(FEATURE_ORDER))
    path = _artifact_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(artifact, f)
    return path


def ensure_model_artifact() -> Path:
    path = _artifact_path()
    if path.exists():
        return path
    return train_and_save()


def train_cli() -> None:
    """Optional entrypoint for manual retraining: `python -m backend.model.train`"""
    p = train_and_save()
    print(f"Saved model to {p}")


if __name__ == "__main__":
    train_cli()

