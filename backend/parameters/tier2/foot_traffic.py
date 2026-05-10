"""
Foot traffic / busyness via Foursquare Places API.
Requires: FOURSQUARE_API_KEY
Falls back to a proxy from restaurant + bar density if key unavailable.
"""
import os
import requests
import networkx as nx
from ..base import BaseParameter, build_point_grid

FSQ_URL = "https://api.foursquare.com/v3/places/search"


class FootTraffic(BaseParameter):
    key = "foot_traffic"

    def load(self, G: nx.MultiDiGraph) -> None:
        api_key = os.getenv("FOURSQUARE_API_KEY")
        if not api_key:
            print(f"  {self.key}: no FOURSQUARE_API_KEY — using restaurant+bar proxy")
            self._proxy_from_existing(G)
            return

        print(f"  Loading {self.key} via Foursquare…")
        try:
            lats = [G.nodes[n]["y"] for n in G.nodes]
            lngs = [G.nodes[n]["x"] for n in G.nodes]
            center_lat = sum(lats) / len(lats)
            center_lng = sum(lngs) / len(lngs)

            headers = {"Authorization": api_key, "accept": "application/json"}
            params = {
                "ll": f"{center_lat},{center_lng}",
                "radius": 15000,
                "categories": "13000,10000",  # food & drink, arts
                "limit": 50,
            }
            resp = requests.get(FSQ_URL, headers=headers, params=params, timeout=15).json()
            points = []
            for r in resp.get("results", []):
                loc = r.get("geocodes", {}).get("main", {})
                if "latitude" in loc:
                    points.append((loc["latitude"], loc["longitude"]))
            grid = build_point_grid(points)
            self._write_from_grid(G, grid, max_val=5.0)
            print(f"    {len(points)} Foursquare venues loaded")
        except Exception as e:
            print(f"    {self.key} failed: {e} — using proxy")
            self._proxy_from_existing(G)

    def _proxy_from_existing(self, G: nx.MultiDiGraph) -> None:
        """Average restaurant + nightlife scores as a busyness proxy."""
        for u, v, k, data in G.edges(keys=True, data=True):
            r = data.get("param_restaurant_density", 0.0)
            n = data.get("param_nightlife_density", 0.0)
            G[u][v][k][f"param_{self.key}"] = (r + n) / 2
