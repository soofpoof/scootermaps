from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.routing import RoutingEngine, NoRouteFound

VALID_PROFILES = {"snorfiets", "bromfiets"}

# Module-level container so the engine is loaded once at startup and reused.
state: dict = {}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("[startup] Loading routing engine — this can take a few seconds.")
    state["engine"] = RoutingEngine()
    g = state["engine"].graph
    print(f"[startup] Graph loaded: {len(g.nodes):,} nodes, {len(g.edges):,} edges.")
    for profile_name, sub in state["engine"].subgraphs.items():
        print(
            f"[startup]   profile={profile_name}: "
            f"{len(sub.nodes):,} legal nodes, {len(sub.edges):,} legal edges"
        )
    yield
    state.clear()


app = FastAPI(title="Scootermaps API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    engine = state.get("engine")
    return {
        "name": "Scootermaps API",
        "version": "0.1.0",
        "profiles": sorted(VALID_PROFILES),
        "graph_nodes": len(engine.graph.nodes) if engine else None,
        "graph_edges": len(engine.graph.edges) if engine else None,
    }


@app.get("/route")
def route(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    profile: str = "snorfiets",
):
    if profile not in VALID_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=f"profile must be one of {sorted(VALID_PROFILES)}",
        )
    engine: RoutingEngine = state.get("engine")
    if engine is None:
        raise HTTPException(status_code=503, detail="Routing engine not ready")

    try:
        return engine.find_route(from_lat, from_lon, to_lat, to_lon, profile)
    except NoRouteFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
