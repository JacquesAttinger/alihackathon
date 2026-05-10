"""Sidewalk presence from OSM sidewalk tag."""
import networkx as nx
from ..base import BaseParameter


class SidewalkQuality(BaseParameter):
    key = "sidewalk_quality"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key} (OSM)…")
        for u, v, k, data in G.edges(keys=True, data=True):
            sw = str(data.get("sidewalk", "")).lower()
            hw = str(data.get("highway", "")).lower()

            if sw in ("both", "yes", "left", "right"):
                score = 1.0
            elif sw == "no":
                score = 0.0
            elif hw in ("footway", "pedestrian", "path"):
                score = 0.9  # it IS the walking surface
            elif hw in ("primary", "secondary", "tertiary", "residential"):
                score = 0.7  # likely has sidewalk even if untagged
            else:
                score = 0.4

            G[u][v][k][f"param_{self.key}"] = score
