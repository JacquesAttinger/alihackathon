"""
Loads Chicago park locations from OpenStreetMap and finds the best
park waypoint for a given route.

Best park = minimises detour:
    detour = haversine(start, park) + haversine(park, end) - haversine(start, end)
"""

import math
import osmnx as ox
import networkx as nx


def _haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_parks() -> list[dict]:
    """Fetch Chicago parks from OSM. Returns list of {name, lat, lng}."""
    print("  Loading Chicago parks from OpenStreetMap…")
    try:
        gdf = ox.features_from_place(
            "Chicago, Illinois, USA",
            tags={"leisure": "park"},
        )
        parks = []
        for _, row in gdf.iterrows():
            try:
                centroid = row.geometry.centroid
                name = row.get("name", "Park") or "Park"
                parks.append({"name": name, "lat": centroid.y, "lng": centroid.x})
            except Exception:
                continue
        print(f"    {len(parks)} parks loaded from OSM")
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
            try:
                node = ox.distance.nearest_nodes(G, park["lng"], park["lat"])
                best_detour = detour
                best_node = node
                best_name = park["name"]
            except Exception:
                continue

    return best_node, best_name
