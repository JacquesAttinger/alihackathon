"""Schools from OSM amenity=school tag. Used as a family-friendly signal."""
import networkx as nx
from ..base import BaseParameter, build_point_grid


class SchoolProximity(BaseParameter):
    key = "school_proximity"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key} (OSM nodes)…")
        points = []
        for node, data in G.nodes(data=True):
            if data.get("amenity") == "school":
                points.append((data["y"], data["x"]))

        if points:
            grid = build_point_grid(points, [2.0] * len(points))
            self._write_from_grid(G, grid, max_val=4.0)
            print(f"    {len(points)} schools found in graph nodes")
        else:
            # Schools are usually in OSM but may not be graph nodes — score 0
            print(f"    No school nodes in graph — defaulting to 0")
            self._write_all(G, 0.0)
