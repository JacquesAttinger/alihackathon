"""
Shared helper for Google Places API (New) calls.
All Tier 2 Google parameters inherit from GooglePlacesBase.
Requires: GOOGLE_PLACES_API_KEY in environment.
Uses the Places API (New) endpoint: places.googleapis.com/v1/places:searchNearby
"""
import os
import requests
import networkx as nx
from ..base import BaseParameter, build_point_grid, CELL_DEG

PLACES_URL = "https://places.googleapis.com/v1/places:searchNearby"

# Map our simple type names to Places API (New) includedTypes values
TYPE_MAP = {
    "restaurant": "restaurant",
    "bar": "bar",
    "cafe": "cafe",
    "establishment": "establishment",
}


def fetch_places(lat: float, lng: float, place_type: str, radius: int, api_key: str, open_now: bool = False) -> list[tuple[float, float]]:
    body = {
        "includedTypes": [TYPE_MAP.get(place_type, place_type)],
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius),
            }
        },
        "maxResultCount": 20,
    }
    if open_now:
        body["openNow"] = True

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.location",
    }

    try:
        resp = requests.post(PLACES_URL, json=body, headers=headers, timeout=15).json()
        return [
            (p["location"]["latitude"], p["location"]["longitude"])
            for p in resp.get("places", [])
            if "location" in p
        ]
    except Exception:
        return []


class GooglePlacesBase(BaseParameter):
    place_type: str = ""
    search_radius: int = 300
    open_now: bool = False
    grid_max: float = 5.0
    sample_every_n_cells: int = 3

    def load(self, G: nx.MultiDiGraph) -> None:
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            print(f"  {self.key}: no GOOGLE_PLACES_API_KEY — defaulting to 0")
            self._write_all(G, 0.0)
            return

        print(f"  Loading {self.key} via Google Places (New)…")
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

        all_points = list(set(all_points))
        grid = build_point_grid(all_points)
        self._write_from_grid(G, grid, max_val=self.grid_max)
        print(f"    {len(all_points)} {self.place_type} places loaded")
