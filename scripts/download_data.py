"""Download the Amsterdam street network from OpenStreetMap and cache it locally.

Run once per development environment:

    python scripts/download_data.py

The result is a GraphML file at data/amsterdam.graphml. Subsequent runs of the
backend load this file from disk in ~1 second, instead of re-hitting Overpass.

We fetch the "drive" network: roads accessible to motor vehicles. Scooters are
required to ride on the road in Amsterdam (snorfiets since 2019, bromfiets
always), so the road graph is the right substrate. Profile rules then further
exclude motorways, restricted-access streets, etc.
"""
from pathlib import Path
import sys
import time

import osmnx as ox


PLACE = "Amsterdam, North Holland, Netherlands"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "amsterdam.graphml"


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if OUT_PATH.exists():
        print(f"[skip] {OUT_PATH} already exists ({OUT_PATH.stat().st_size / 1e6:.1f} MB)")
        return

    print(f"[fetch] Downloading street network for: {PLACE}")
    start = time.time()
    graph = ox.graph_from_place(PLACE, network_type="drive", retain_all=False)
    elapsed = time.time() - start
    print(
        f"[fetch] Got {len(graph.nodes):,} nodes and {len(graph.edges):,} edges "
        f"in {elapsed:.1f}s"
    )

    print(f"[save]  Writing to {OUT_PATH}")
    ox.save_graphml(graph, OUT_PATH)
    print(f"[done]  {OUT_PATH.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
