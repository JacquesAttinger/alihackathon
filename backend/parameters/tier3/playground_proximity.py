"""Playgrounds from OSM leisure=playground tag."""
import networkx as nx
from ..base import BaseParameter, build_point_grid


class PlaygroundProximity(BaseParameter):
    key = "playground_proximity"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key} (OSM nodes)…")
        points = []
        for node, data in G.nodes(data=True):
            if data.get("leisure") == "playground":
                points.append((data["y"], data["x"]))

        if points:
            grid = build_point_grid(points, [2.0] * len(points))
            self._write_from_grid(G, grid, max_val=4.0)
            print(f"    {len(points)} playgrounds found")
        else:
            self._write_all(G, 0.0)
