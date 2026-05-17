"""Custom shortest-path routing for Amsterdam scooters on an OSM street graph.

Load order at startup:
  1. Load the cached GraphML from data/amsterdam.graphml.
  2. Annotate every edge with a travel-time-in-seconds per profile
     (forbidden edges get None and are dropped from the profile-specific
     subgraph at the next step).
  3. Build a profile-specific subgraph per scooter type — the routing call
     then runs Dijkstra over just the legal edges for that profile.

This module exposes a single class — `RoutingEngine` — that the FastAPI app
instantiates once at startup and reuses across requests.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import networkx as nx
import osmnx as ox
from shapely.geometry import LineString

from .profiles import PROFILES


GRAPH_PATH = Path(__file__).resolve().parents[2] / "data" / "amsterdam.graphml"


class NoRouteFound(Exception):
    """Raised when there is no legal path for the requested profile."""


class RoutingEngine:
    """Routing engine for a single OSM graph, with profile-aware subgraphs."""

    def __init__(self, graph_path: Path = GRAPH_PATH):
        if not graph_path.exists():
            raise FileNotFoundError(
                f"Graph file not found at {graph_path}. "
                "Run `python scripts/download_data.py` first."
            )
        self.graph = ox.load_graphml(graph_path)
        self._annotate_weights()
        self.subgraphs: dict[str, nx.MultiDiGraph] = self._build_subgraphs()

    def _annotate_weights(self) -> None:
        """For each edge, set `time_<profile>` to travel time in seconds, or None if forbidden."""
        for _u, _v, _k, data in self.graph.edges(keys=True, data=True):
            try:
                length_m = float(data.get("length", 0.0))
            except (TypeError, ValueError):
                length_m = 0.0
            for profile_name, speed_fn in PROFILES.items():
                speed_kmh = speed_fn(data)
                attr = f"time_{profile_name}"
                if speed_kmh is None or speed_kmh <= 0:
                    data[attr] = None
                else:
                    # length_m / (km/h * 1000/3600) = seconds
                    data[attr] = length_m / (speed_kmh * 1000.0 / 3600.0)

    def _build_subgraphs(self) -> dict[str, nx.MultiDiGraph]:
        """Materialize a per-profile subgraph containing only legal edges."""
        subgraphs: dict[str, nx.MultiDiGraph] = {}
        for profile_name in PROFILES:
            attr = f"time_{profile_name}"
            legal_edges = [
                (u, v, k)
                for u, v, k, data in self.graph.edges(keys=True, data=True)
                if data.get(attr) is not None
            ]
            view = self.graph.edge_subgraph(legal_edges)
            subgraphs[profile_name] = view.copy()
        return subgraphs

    def find_route(
        self,
        from_lat: float,
        from_lon: float,
        to_lat: float,
        to_lon: float,
        profile: str,
    ) -> dict:
        if profile not in PROFILES:
            raise ValueError(f"Unknown profile: {profile!r}")

        sub = self.subgraphs[profile]
        attr = f"time_{profile}"

        # Snap to the nearest node *within the legal subgraph* so we never
        # start on a forbidden segment.
        try:
            orig = ox.nearest_nodes(sub, from_lon, from_lat)
            dest = ox.nearest_nodes(sub, to_lon, to_lat)
        except Exception as exc:  # noqa: BLE001
            raise NoRouteFound(f"Could not snap to network: {exc}") from exc

        if orig == dest:
            raise NoRouteFound(
                "Start and end resolve to the same network node — try points further apart."
            )

        try:
            path = nx.shortest_path(sub, orig, dest, weight=attr)
        except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
            raise NoRouteFound(f"No legal path: {exc}") from exc

        coords, total_dist_m, total_time_s = self._reconstruct_geometry(sub, path, attr)

        return {
            "profile": profile,
            "geometry": {
                "type": "LineString",
                "coordinates": [[round(x, 6), round(y, 6)] for x, y in coords],
            },
            "distance_m": round(total_dist_m, 1),
            "duration_s": round(total_time_s, 1),
            "note": None,
        }

    def _reconstruct_geometry(
        self,
        sub: nx.MultiDiGraph,
        path: list,
        weight_attr: str,
    ) -> tuple[list[tuple[float, float]], float, float]:
        """Walk the node path and stitch together edge geometries."""
        coords: list[tuple[float, float]] = []
        total_dist = 0.0
        total_time = 0.0

        for u, v in zip(path[:-1], path[1:]):
            parallel = sub.get_edge_data(u, v)
            if not parallel:
                raise NoRouteFound(f"Missing edge {u}→{v} in subgraph")

            # Pick the parallel edge with the lowest travel time
            best_key, best_time = None, None
            for key, data in parallel.items():
                t = data.get(weight_attr)
                if t is None:
                    continue
                if best_time is None or t < best_time:
                    best_key, best_time = key, t
            if best_key is None:
                raise NoRouteFound(f"No legal parallel edge {u}→{v}")

            data = parallel[best_key]
            total_time += best_time
            try:
                total_dist += float(data.get("length", 0.0))
            except (TypeError, ValueError):
                pass

            geom: Optional[LineString] = data.get("geometry")
            if isinstance(geom, LineString):
                pts = [(x, y) for x, y in geom.coords]
            else:
                pts = [
                    (float(sub.nodes[u]["x"]), float(sub.nodes[u]["y"])),
                    (float(sub.nodes[v]["x"]), float(sub.nodes[v]["y"])),
                ]

            if coords and coords[-1] == pts[0]:
                coords.extend(pts[1:])
            else:
                coords.extend(pts)

        return coords, total_dist, total_time
