import base64
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


class ScreenshotPayload(BaseModel):
    name: str
    data_url: str
    subdir: str = "demo/week1"


@app.post("/screenshot")
def save_screenshot(payload: ScreenshotPayload):
    """Save a base64 PNG/JPEG data URL under demo/week1/<name>.png.

    Used by the front-end demo helper to capture the map canvas without
    needing OS-level window focus juggling.
    """
    if not payload.data_url.startswith("data:image/"):
        raise HTTPException(400, "expected a data:image/... URL")
    if "," not in payload.data_url:
        raise HTTPException(400, "malformed data URL")
    _, b64 = payload.data_url.split(",", 1)
    try:
        raw = base64.b64decode(b64)
    except Exception as exc:
        raise HTTPException(400, f"base64 decode failed: {exc}") from exc

    # Lock the destination to the project's demo tree to prevent path escapes.
    project_root = Path(__file__).resolve().parents[1]
    safe_subdir = Path(payload.subdir)
    if safe_subdir.is_absolute() or ".." in safe_subdir.parts:
        raise HTTPException(400, "subdir must be a relative path inside the project")
    safe_name = Path(payload.name).name  # strip any path components
    if not safe_name:
        raise HTTPException(400, "name is empty")

    out_dir = project_root / safe_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{safe_name}.png"
    out_path.write_bytes(raw)
    return {"saved": str(out_path.relative_to(project_root)), "bytes": len(raw)}


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
