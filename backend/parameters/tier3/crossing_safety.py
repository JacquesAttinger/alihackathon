"""Signalized vs. unmarked crosswalks from OSM crossing tag."""
import networkx as nx
from ..base import BaseParameter


class CrossingSafety(BaseParameter):
    key = "crossing_safety"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key} (OSM)…")
        for u, v, k, data in G.edges(keys=True, data=True):
            crossing = str(data.get("crossing", "")).lower()
            if "traffic_signals" in crossing or "pelican" in crossing or "toucan" in crossing:
                score = 1.0
            elif "marked" in crossing or "zebra" in crossing:
                score = 0.7
            elif "uncontrolled" in crossing:
                score = 0.3
            elif crossing == "no" or crossing == "":
                score = 0.5  # no crossing tag = unknown
            else:
                score = 0.4
            G[u][v][k][f"param_{self.key}"] = score
