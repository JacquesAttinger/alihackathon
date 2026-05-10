"""
CTA L station locations from Chicago Data Portal.
Dataset: CTA - 'L' (Rail) Stations
Requires: no API key
"""
import requests
import networkx as nx
from ..base import BaseParameter, build_point_grid

URL = (
    "https://data.cityofchicago.org/resource/8pix-ypme.json"
    "?$limit=200&$select=location"
)


class TransitProximity(BaseParameter):
    key = "transit_proximity"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key}…")
        try:
            rows = requests.get(URL, timeout=30).json()
            points = []
            for r in rows:
                try:
                    loc = r["location"]
                    points.append((float(loc["latitude"]), float(loc["longitude"])))
                except (KeyError, TypeError, ValueError):
                    continue
            if not points:
                raise ValueError("empty dataset")
            # L stops have influence ~400m; give them weight 4
            grid = build_point_grid(points, [4.0] * len(points))
            self._write_from_grid(G, grid, max_val=8.0)
            print(f"    {len(points)} CTA L stations loaded")
        except Exception as e:
            print(f"    {self.key} failed: {e} — defaulting to 0")
            self._write_all(G, 0.0)
