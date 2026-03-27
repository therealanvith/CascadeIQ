# CascadeIQ — Vessel Delay Cascade Predictor

CascadeIQ predicts vessel delay risk (ML) and simulates how that delay cascades through a downstream supply chain (graph propagation) for the DP World Hackathon demo.

## Architecture
- **Frontend**: Next.js + Tailwind + Leaflet map
- **Backend**: Python FastAPI
- **ML**: XGBoost classifier + regressor trained on **real AIS features** (MarineTraffic API and/or your own CSV export)
- **Graph**: NetworkX directed graph cascade simulation

### Important: MarineTraffic data (no fake / no scraping)
- **Do not scrape** the MarineTraffic website map URL — it is not a stable API, may violate ToS, and is unreliable for training.
- This project pulls **real AIS data via the official MarineTraffic HTTP API** using `MARINETRAFFIC_API_KEY` (see `https://servicedocs.marinetraffic.com/`).
- Weather features use **Open-Meteo** (no key) for wind-based `weather_severity` at vessel coordinates.
- Training labels use `delta = max(0, ETA - ETA_CALC)` in hours when both timestamps exist in the extended AIS payload.

## Local setup

### 1) Backend (FastAPI)
From repo root:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
```

Copy `env.example` to `.env` in the repo root (or export variables in your shell) and set **`MARINETRAFFIC_API_KEY`** *or* **`AIS_TRAINING_CSV`**.

Then:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

On first startup, if `backend/model/vessel_delay_model.pkl` does not exist, the server will **fetch real AIS training rows** (or load your CSV) and train the model.

### Train manually (optional)

```bash
python -m backend.model.train
```

### 2) Frontend (Next.js)
In a second terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Run:

```bash
npm run dev
```

Open `http://localhost:3000`.

## Demo flow (hackathon)
1. Open **Dashboard** → see vessels on the map + risk
2. Click **Cascade** → select **MV Endeavour** and set delay to **14h**
3. Run simulation → view affected nodes + SLA breach + recommendations

## API (backend)
- `GET /vessels`
- `POST /predict`
- `POST /cascade`
- `GET /graph`

## Deployment (free tiers)

### Backend on Render
- Create a new **Web Service**
- Build command:

```bash
pip install -r backend/requirements.txt
```

- Start command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

- Env vars:
  - `FRONTEND_ORIGIN`: your Vercel URL (comma-separated allowed)
  - `MARINETRAFFIC_API_KEY` **or** `AIS_TRAINING_CSV` (required for first-time training)
  - Optional: `MODEL_PATH`: custom model file path
  - Optional: `MARINETRAFFIC_CENTER_LAT`, `MARINETRAFFIC_CENTER_LON`, `MARINETRAFFIC_RING_COUNT`

### Frontend on Vercel
- Import the `frontend/` project
- Set env var:
  - `NEXT_PUBLIC_API_BASE_URL`: your Render backend URL (e.g. `https://your-service.onrender.com`)

