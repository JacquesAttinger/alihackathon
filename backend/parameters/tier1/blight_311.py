"""
Chicago 311 service requests as a neighborhood blight proxy.
Uses: graffiti removal, abandoned vehicles, sanitation complaints.
Dataset: 311 Service Requests (2018-present)
Requires: no API key
"""
import requests
import networkx as nx
from ..base import BaseParameter, build_point_grid

URL = (
    "https://data.cityofchicago.org/resource/v6vf-nfxy.json"
    "?$limit=50000"
    "&$where=created_date>='2023-01-01'"
    "&$select=latitude,longitude,sr_type"
)

BLIGHT_TYPES = {"Graffiti Removal", "Abandoned Vehicle", "Rodent Baiting", "Sanitation"}


class Blight311(BaseParameter):
    key = "blight_311"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key}…")
        try:
            rows = requests.get(URL, timeout=30).json()
            points = []
            for r in rows:
                try:
                    if not any(b in r.get("sr_type", "") for b in BLIGHT_TYPES):
                        continue
                    points.append((float(r["latitude"]), float(r["longitude"])))
                except (KeyError, ValueError, TypeError):
                    continue
            if not points:
                raise ValueError("empty dataset")
            grid = build_point_grid(points)
            self._write_from_grid(G, grid, max_val=10.0)
            print(f"    {len(points)} 311 blight complaints loaded")
        except Exception as e:
            print(f"    {self.key} failed: {e} — defaulting to 0")
            self._write_all(G, 0.0)
