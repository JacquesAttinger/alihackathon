"""
Chicago park locations from the Chicago Park District open data.
Requires: no API key
"""
import requests
import networkx as nx
from ..base import BaseParameter, build_point_grid

URL = (
    "https://data.cityofchicago.org/resource/ej32-qgdr.json"
    "?$limit=1000&$select=location"
)


class ParkProximity(BaseParameter):
    key = "park_proximity"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key}…")
        try:
            rows = requests.get(URL, timeout=30).json()
            points = []
            for r in rows:
                try:
                    coords = r["location"]["coordinates"]  # [lng, lat]
                    points.append((float(coords[1]), float(coords[0])))
                except (KeyError, TypeError, IndexError, ValueError):
                    continue
            if not points:
                raise ValueError("empty dataset")
            # Parks are large features; use radius_cells=3 (~600m) in grid lookup
            grid = build_point_grid(points, [3.0] * len(points))
            self._write_from_grid(G, grid, max_val=6.0)
            print(f"    {len(points)} parks loaded")
        except Exception as e:
            print(f"    {self.key} failed: {e} — using OSM leisure tags")
            self._proxy_from_osm(G)

    def _proxy_from_osm(self, G: nx.MultiDiGraph) -> None:
        for u, v, k, data in G.edges(keys=True, data=True):
            leisure = str(data.get("leisure", "")).lower()
            score = 0.8 if "park" in leisure or "garden" in leisure else 0.0
            G[u][v][k][f"param_{self.key}"] = score
