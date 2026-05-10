"""
scenic_quality parameter.

Sources (in order of contribution):
  1. Chicago Park District locations — Chicago Data Portal (no API key needed)
  2. Chicago tree inventory        — Chicago Data Portal (no API key needed)
  3. Lakefront / Riverwalk tags    — OpenStreetMap edge attributes (no API key needed)

Score per edge: 0.0 (no greenery) → 1.0 (lakefront trail next to a park full of trees)
"""
import requests
import networkx as nx
from .base import BaseParameter, build_point_grid, grid_score_at, edge_midpoint, CELL_DEG

PARKS_URL = (
    "https://data.cityofchicago.org/resource/ej32-qgdr.json"
    "?$limit=1000&$select=location"
)
TREES_URL = (
    "https://data.cityofchicago.org/resource/y8vk-w5kv.json"
    "?$limit=50000&$select=latitude,longitude,condition"
)

LAKEFRONT_KEYWORDS = {"lakefront", "lake shore", "riverwalk", "river walk", "chicago river"}

TREE_CONDITION_SCORES = {"excellent": 1.0, "good": 0.8, "fair": 0.5, "poor": 0.2}


def _fetch_parks() -> list[tuple[float, float]]:
    try:
        rows = requests.get(PARKS_URL, timeout=30).json()
        points = []
        for r in rows:
            try:
                coords = r["location"]["coordinates"]  # [lng, lat]
                points.append((float(coords[1]), float(coords[0])))
            except (KeyError, TypeError, IndexError, ValueError):
                continue
        print(f"    {len(points)} Chicago parks loaded")
        return points
    except Exception as e:
        print(f"    Parks fetch failed: {e}")
        return []


def _fetch_trees() -> list[tuple[tuple[float, float], float]]:
    try:
        rows = requests.get(TREES_URL, timeout=30).json()
        results = []
        for r in rows:
            try:
                lat, lng = float(r["latitude"]), float(r["longitude"])
                score = TREE_CONDITION_SCORES.get(r.get("condition", "good").lower(), 0.6)
                results.append(((lat, lng), score))
            except (KeyError, ValueError, TypeError):
                continue
        print(f"    {len(results)} trees loaded")
        return results
    except Exception as e:
        print(f"    Trees fetch failed: {e}")
        return []


def _lakefront_score(data: dict) -> float:
    name = str(data.get("name", "")).lower()
    ref  = str(data.get("ref", "")).lower()
    hw   = str(data.get("highway", "")).lower()
    combined = f"{name} {ref}"
    if any(kw in combined for kw in LAKEFRONT_KEYWORDS):
        return 1.0
    if hw in ("path", "footway", "pedestrian") and "lake" in combined:
        return 0.6
    return 0.0


class ScenicQuality(BaseParameter):
    key = "scenic_quality"

    def load(self, G: nx.MultiDiGraph) -> None:
        print("  Loading scenic_quality…")

        # --- Data fetching ---
        park_points = _fetch_parks()
        tree_data   = _fetch_trees()

        # Parks are large; give each a high weight and wide spatial influence
        park_grid = build_point_grid(park_points, [4.0] * len(park_points))
        tree_grid = build_point_grid(
            [pt for pt, _ in tree_data],
            [v  for _, v  in tree_data],
        )

        # --- Score each edge ---
        for u, v, k, data in G.edges(keys=True, data=True):
            lat, lng = edge_midpoint(G, u, v)

            # Park contribution: nearby parks score up to 1.0 (cap at 6 grid units)
            park_score = min(grid_score_at(lat, lng, park_grid, radius_cells=2) / 6.0, 1.0)

            # Tree contribution: dense healthy trees score up to 1.0 (cap at 10 units)
            tree_score = min(grid_score_at(lat, lng, tree_grid, radius_cells=1) / 10.0, 1.0)

            # Lakefront/riverwalk: binary boost from OSM tags
            lake_score = _lakefront_score(data)

            # Combine: lakefront is the strongest signal, then parks, then trees
            scenic = lake_score * 0.5 + park_score * 0.35 + tree_score * 0.15

            G[u][v][k]["param_scenic_quality"] = min(scenic, 1.0)

        print("  scenic_quality done.")
