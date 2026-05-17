"""Edge-allowance and speed rules per scooter type, derived from Dutch traffic law.

Each profile is a function that takes a dict of OSM edge attributes and returns
either a speed in km/h (edge is legal at that speed) or None (edge is forbidden
for this scooter type). The routing engine converts speed to a travel-time
weight (seconds) and runs shortest-time-path over the legal subgraph.

Reference (simplified for v0):

**Snorfiets** — blauw kenteken, max 25 km/h:
    - Must ride on the road in Amsterdam since 2019 (no fietspad).
    - Helmplicht since 2023.
    - Allowed road classes: residential, tertiary, secondary, primary,
      living_street, unclassified, service.
    - Forbidden: motorway, motorway_link, trunk, trunk_link.
    - Forbidden non-road: cycleway, footway, pedestrian, path, steps.
    - Speed capped at 25 km/h everywhere; 15 km/h in woonerf (living_street).

**Bromfiets** — geel kenteken, max 45 km/h:
    - Must ride on the road (always).
    - Same allowed/forbidden classes as snorfiets.
    - Speed follows the posted maxspeed tag, capped at 45 km/h; 30 km/h is the
      sensible default for residential streets.
"""
from __future__ import annotations

import ast
from typing import Optional


FORBIDDEN_HIGHWAYS = frozenset(
    {
        "motorway",
        "motorway_link",
        "trunk",
        "trunk_link",
        "cycleway",
        "footway",
        "pedestrian",
        "path",
        "steps",
        "track",
        "bridleway",
        "construction",
        "raceway",
        "proposed",
    }
)


def _first(value):
    """Normalize OSM tag values that may be lists, stringified lists, or scalars.

    osmnx serializes some tag values to GraphML as the string form of a list
    (e.g. "['residential', 'living_street']") — be defensive on read.
    """
    if value is None:
        return None
    if isinstance(value, list):
        return value[0] if value else None
    if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed[0] if parsed else None
        except (ValueError, SyntaxError):
            return value
    return value


def _parse_maxspeed(raw) -> Optional[float]:
    """Best-effort parse of OSM maxspeed values into km/h."""
    raw = _first(raw)
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if not s:
        return None
    parts = s.replace("km/h", "").replace("kmh", "").strip().split()
    try:
        return float(parts[0])
    except (ValueError, IndexError):
        return None


def _is_forbidden(tags: dict) -> bool:
    highway = _first(tags.get("highway"))
    if highway in FORBIDDEN_HIGHWAYS:
        return True
    if _first(tags.get("access")) in {"no", "private"}:
        return True
    if _first(tags.get("motor_vehicle")) == "no":
        return True
    if _first(tags.get("moped")) == "no":
        return True
    return False


def snorfiets_speed_kmh(tags: dict) -> Optional[float]:
    """Snorfiets: hard 25 km/h cap, road-only. Returns None if forbidden."""
    if _is_forbidden(tags):
        return None
    if _first(tags.get("highway")) == "living_street":
        return 15.0
    return 25.0


def bromfiets_speed_kmh(tags: dict) -> Optional[float]:
    """Bromfiets: 45 km/h cap, follows posted limit when present."""
    if _is_forbidden(tags):
        return None
    highway = _first(tags.get("highway"))
    if highway == "living_street":
        return 15.0
    posted = _parse_maxspeed(tags.get("maxspeed"))
    if posted is not None:
        return min(45.0, posted)
    if highway in {"residential", "tertiary", "unclassified", "service"}:
        return 30.0
    return 45.0


PROFILES = {
    "snorfiets": snorfiets_speed_kmh,
    "bromfiets": bromfiets_speed_kmh,
}
