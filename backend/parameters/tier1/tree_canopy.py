"""
Chicago tree inventory — individual tree locations with species and condition.
Dataset: https://data.cityofchicago.org/resource/y8vk-w5kv.json
Requires: no API key (public Socrata, large dataset — sampled to 50k)
"""
import requests
import networkx as nx
from ..base import BaseParameter, build_point_grid

URL = (
    "https://data.cityofchicago.org/resource/y8vk-w5kv.json"
    "?$limit=50000&$select=latitude,longitude,condition"
)


class TreeCanopy(BaseParameter):
    key = "tree_canopy"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key}…")
        try:
            rows = requests.get(URL, timeout=30).json()
            points, values = [], []
            condition_scores = {"excellent": 1.0, "good": 0.8, "fair": 0.5, "poor": 0.2}
            for r in rows:
                try:
                    lat, lng = float(r["latitude"]), float(r["longitude"])
                    cond = r.get("condition", "good").lower()
                    val = condition_scores.get(cond, 0.6)
                    points.append((lat, lng))
                    values.append(val)
                except (KeyError, ValueError, TypeError):
                    continue
            if not points:
                raise ValueError("empty dataset")
            grid = build_point_grid(points, values)
            self._write_from_grid(G, grid, max_val=8.0)
            print(f"    {len(points)} trees loaded")
        except Exception as e:
            print(f"    {self.key} failed: {e} — defaulting to 0")
            self._write_all(G, 0.0)
