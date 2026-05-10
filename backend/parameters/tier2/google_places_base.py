"""
Shared helper for Google Places API calls.
All Tier 2 Google parameters inherit from GooglePlacesBase.
Requires: GOOGLE_PLACES_API_KEY in environment.
"""
import os
import requests
import networkx as nx
from ..base import BaseParameter, build_point_grid, edge_midpoint, CELL_DEG

PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


def fetch_places(lat: float, lng: float, place_type: str, radius: int, api_key: str, open_now: bool = False) -> list[tuple[float, float]]:
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": place_type,
        "key": api_key,
    }
    if open_now:
        params["opennow"] = "true"
    results = []
    while True:
        resp = requests.get(PLACES_URL, params=params, timeout=15).json()
        for r in resp.get("results", []):
            loc = r["geometry"]["location"]
            results.append((loc["lat"], loc["lng"]))
        token = resp.get("next_page_token")
        if not token:
            break
        params = {"pagetoken": token, "key": api_key}
    return results


class GooglePlacesBase(BaseParameter):
    place_type: str = ""
    search_radius: int = 300
    open_now: bool = False
    grid_max: float = 5.0
    sample_every_n_cells: int = 3  # only query every Nth grid cell to save API calls

    def load(self, G: nx.MultiDiGraph) -> None:
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            print(f"  {self.key}: no GOOGLE_PLACES_API_KEY — defaulting to 0")
            self._write_all(G, 0.0)
            return

        print(f"  Loading {self.key} via Google Places…")
        # Sample the bounding box at coarse grid resolution to limit API calls
        lats = [G.nodes[n]["y"] for n in G.nodes]
        lngs = [G.nodes[n]["x"] for n in G.nodes]
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)

        all_points: list[tuple[float, float]] = []
        step = CELL_DEG * self.sample_every_n_cells
        lat = min_lat
        while lat <= max_lat:
            lng = min_lng
            while lng <= max_lng:
                pts = fetch_places(lat, lng, self.place_type, self.search_radius, api_key, self.open_now)
                all_points.extend(pts)
                lng += step
            lat += step

        # Deduplicate
        all_points = list(set(all_points))
        grid = build_point_grid(all_points)
        self._write_from_grid(G, grid, max_val=self.grid_max)
        print(f"    {len(all_points)} {self.place_type} places loaded")
