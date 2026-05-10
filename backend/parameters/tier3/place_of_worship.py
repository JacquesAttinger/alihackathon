"""Places of worship as community anchor points (OSM amenity=place_of_worship)."""
import networkx as nx
from ..base import BaseParameter, build_point_grid


class PlaceOfWorship(BaseParameter):
    key = "place_of_worship"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key} (OSM nodes)…")
        points = []
        for node, data in G.nodes(data=True):
            if data.get("amenity") == "place_of_worship":
                points.append((data["y"], data["x"]))

        if points:
            grid = build_point_grid(points, [1.5] * len(points))
            self._write_from_grid(G, grid, max_val=3.0)
            print(f"    {len(points)} places of worship found")
        else:
            self._write_all(G, 0.0)
