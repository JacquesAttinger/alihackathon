import requests
import networkx as nx
from ..base import BaseParameter, build_point_grid

PROPERTY_TYPES = {"THEFT", "BURGLARY", "MOTOR VEHICLE THEFT", "CRIMINAL DAMAGE", "ARSON"}

URL = (
    "https://data.cityofchicago.org/resource/ijzp-q8t2.json"
    "?$limit=50000&$where=year>=2023"
    "&$select=latitude,longitude,primary_type"
)


class PropertyCrime(BaseParameter):
    key = "property_crime"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key}…")
        try:
            rows = requests.get(URL, timeout=30).json()
            points = []
            for r in rows:
                try:
                    if r.get("primary_type", "").upper() not in PROPERTY_TYPES:
                        continue
                    points.append((float(r["latitude"]), float(r["longitude"])))
                except (KeyError, ValueError, TypeError):
                    continue
            grid = build_point_grid(points)
            self._write_from_grid(G, grid, max_val=15.0)
            print(f"    {len(points)} property crime incidents loaded")
        except Exception as e:
            print(f"    {self.key} failed: {e} — defaulting to 0")
            self._write_all(G, 0.0)
