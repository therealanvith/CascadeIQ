from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from graph.engine import build_supply_chain_graph, run_cascade
from model.inference import DelayModelBundle
from model.schema import PredictRequest
from model.train import ensure_model_artifact
from vessels import DEMO_VESSELS, list_vessels_with_risk

load_dotenv()


def _get_allowed_origins() -> list[str]:
    # Comma-separated list; allow localhost by default for dev.
    raw = os.getenv("FRONTEND_ORIGIN", "").strip()
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    origins.extend(
        [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://cascadeiq-omega.vercel.app/"
        ]
    )
    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for o in origins:
        if o not in seen:
            out.append(o)
            seen.add(o)
    return out


app = FastAPI(title="CascadeIQ API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    # Ensure the model artifact exists so /predict works end-to-end.
    ensure_model_artifact()


@app.get("/vessels")
def get_vessels() -> dict[str, Any]:
    vessels = list_vessels_with_risk(model=DelayModelBundle, vessels=DEMO_VESSELS)
    return {"vessels": vessels}


@app.post("/predict")
def post_predict(req: PredictRequest) -> dict[str, float]:
    pred = DelayModelBundle.predict(req)
    return {
        "delay_probability": float(pred["delay_probability"]),
        "estimated_delay_hours": float(pred["estimated_delay_hours"]),
    }


@app.get("/graph")
def get_graph() -> dict[str, Any]:
    g = build_supply_chain_graph()
    nodes = []
    for n, attrs in g.nodes(data=True):
        nodes.append({"id": n, **attrs})
    edges = []
    for u, v, attrs in g.edges(data=True):
        edges.append({"source": u, "target": v, **attrs})
    return {"nodes": nodes, "edges": edges}


@app.post("/cascade")
def post_cascade(payload: dict[str, Any]) -> dict[str, Any]:
    vessel_id = str(payload.get("vessel_id", "")).strip()
    delay_hours = float(payload.get("delay_hours", 0.0))
    g = build_supply_chain_graph()
    result = run_cascade(g=g, vessel_id=vessel_id, delay_hours=delay_hours)
    return result

