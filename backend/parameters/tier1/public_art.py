"""
Chicago public art locations (murals, sculptures, installations).
Dataset: https://data.cityofchicago.org/resource/sj6t-9cju.json
Requires: no API key
"""
import requests
import networkx as nx
from ..base import BaseParameter, build_point_grid

URL = (
    "https://data.cityofchicago.org/resource/sj6t-9cju.json"
    "?$limit=5000&$select=latitude,longitude"
)


class PublicArt(BaseParameter):
    key = "public_art"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key}…")
        try:
            rows = requests.get(URL, timeout=30).json()
            points = []
            for r in rows:
                try:
                    points.append((float(r["latitude"]), float(r["longitude"])))
                except (KeyError, ValueError, TypeError):
                    continue
            if not points:
                raise ValueError("empty dataset")
            grid = build_point_grid(points, [2.0] * len(points))
            self._write_from_grid(G, grid, max_val=4.0)
            print(f"    {len(points)} public art locations loaded")
        except Exception as e:
            print(f"    {self.key} failed: {e} — defaulting to 0")
            self._write_all(G, 0.0)
