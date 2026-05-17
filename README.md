# Scootermaps

> Custom routing for snorscooters and bromfietsen in Amsterdam, where Google Maps fails.

## The problem

In Amsterdam, Google Maps offers two routing modes that matter for scooters, and **neither is correct**:

- **Car routing** uses highways and car-only streets — illegal for scooters and often dangerous.
- **Bike routing** uses the fietspad network — illegal for snorfietsen since 2019, and a serious safety hazard on slippery tram tracks.

There is no third option. Riders improvise, break the law, or get pushed onto unsafe routes.

## What this is

A purpose-built routing engine for two Dutch scooter classes:

| Type | Plate | Speed | Where it can ride |
|---|---|---|---|
| **Snorfiets** | Blauw | 25 km/h | On-road only since 2019; helmplicht since 2023 |
| **Bromfiets** | Geel | 45 km/h | On-road only (always) |

The engine is built on top of OpenStreetMap data for Amsterdam, with a modified A\* algorithm and edge weights that reflect Dutch traffic law per scooter type. Extra safety penalties are applied at tram-track crossings, and no-scooter zones (e.g. parts of the binnenstad) are excluded entirely.

## How to run it locally

This is a portfolio project — it runs locally, not on a deployed server.

**Prerequisites:** Python 3.11+ and git. That's it.

```powershell
# 1. Clone and enter the project
git clone https://github.com/<your-username>/scootermaps.git
cd scootermaps

# 2. Set up the Python environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Start the backend (in one terminal)
uvicorn backend.main:app --reload

# 4. Serve the frontend (in a second terminal)
cd frontend
python -m http.server 5500

# 5. Open http://localhost:5500 in your browser
```

## What's inside

- [`backend/`](./backend/) — FastAPI server, custom routing engine
- [`frontend/`](./frontend/) — vanilla HTML/JS map UI
- [`notebooks/`](./notebooks/) — quantitative analysis: how often is Google's bike routing actually legal for a snorfiets? plus a learned route-ranking model
- [`BUSINESS.md`](./BUSINESS.md) — market sizing, user segments, monetization, go-to-market
- [`DECISIONS.md`](./DECISIONS.md) — architecture decisions log

## Roadmap

- **Week 1** — App skeleton with custom snorfiets routing on real OSM data
- **Week 2** — Bromfiets profile, tram-track penalty, no-scooter-zone exclusion, visual polish
- **Week 3** — Quantitative analysis notebook + trained re-ranking model
- **Week 4** — Business case, pitch deck, demo video

---

Built in Amsterdam, by someone who actually rides one of these things.
