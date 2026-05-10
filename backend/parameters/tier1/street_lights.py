"""
Street light locations from Chicago Data Portal.
Dataset: Street Lights - All Out (reports of outages give us light locations).
We use presence of lights as a "prefer" signal.
Requires: no API key (public Socrata dataset)
"""
import requests
import networkx as nx
from ..base import BaseParameter, build_point_grid

# Street light asset locations (each row is a light pole)
URL = (
    "https://data.cityofchicago.org/resource/de85-7xfb.json"
    "?$limit=50000&$select=latitude,longitude"
)


class StreetLights(BaseParameter):
    key = "street_lights"

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
            grid = build_point_grid(points)
            self._write_from_grid(G, grid, max_val=5.0)
            print(f"    {len(points)} street light locations loaded")
        except Exception as e:
            print(f"    {self.key} failed: {e} — using road-type proxy")
            self._proxy_from_road_type(G)

    def _proxy_from_road_type(self, G: nx.MultiDiGraph) -> None:
        """Fallback: major roads assumed lit."""
        well_lit = {"primary", "secondary", "tertiary", "residential"}
        for u, v, k, data in G.edges(keys=True, data=True):
            hw = str(data.get("highway", "")).lower()
            score = 0.9 if any(t in hw for t in well_lit) else 0.3
            G[u][v][k][f"param_{self.key}"] = score
