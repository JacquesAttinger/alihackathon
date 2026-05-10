"""
Loads Chicago park locations and finds the best park waypoint for a route.

Best park = the one that minimises the detour:
    detour = haversine(start, park) + haversine(park, end) - haversine(start, end)

We use straight-line distance for the selection (fast, O(n_parks)),
then do the actual graph routing through the chosen park node.
"""

import math
import requests
import networkx as nx
import osmnx as ox

PARKS_URL = (
    "https://data.cityofchicago.org/resource/ej32-qgdr.json"
    "?$limit=1000&$select=park,location"
)


def _haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_parks() -> list[dict]:
    """Returns list of {name, lat, lng} for all Chicago parks."""
    print("  Loading Chicago parks…")
    try:
        rows = requests.get(PARKS_URL, timeout=30).json()
        parks = []
        for r in rows:
            try:
                coords = r["location"]["coordinates"]  # [lng, lat]
                parks.append({
                    "name": r.get("park", "Park"),
                    "lat": float(coords[1]),
                    "lng": float(coords[0]),
                })
            except (KeyError, TypeError, IndexError, ValueError):
                continue
        print(f"    {len(parks)} parks loaded")
        return parks
    except Exception as e:
        print(f"    Parks load failed: {e}")
        return []


def best_park_node(
    G: nx.MultiDiGraph,
    parks: list[dict],
    start_lat: float, start_lng: float,
    end_lat: float,   end_lng: float,
) -> tuple[int, str] | tuple[None, None]:
    """
    Returns (graph_node_id, park_name) for the park that adds the least detour.
    Returns (None, None) if parks list is empty.
    """
    if not parks:
        return None, None

    direct = _haversine(start_lat, start_lng, end_lat, end_lng)

    best_node, best_name, best_detour = None, None, float("inf")

    for park in parks:
        detour = (
            _haversine(start_lat, start_lng, park["lat"], park["lng"])
            + _haversine(park["lat"], park["lng"], end_lat, end_lng)
            - direct
        )
        if detour < best_detour:
            best_detour = detour
            best_name = park["name"]
            try:
                best_node = ox.distance.nearest_nodes(G, park["lng"], park["lat"])
            except Exception:
                continue

    return best_node, best_name
