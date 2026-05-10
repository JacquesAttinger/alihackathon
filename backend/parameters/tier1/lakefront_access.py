"""
Detects segments on or near the Chicago Lakefront Trail and Riverwalk
using OSM tags. No external API needed.
"""
import networkx as nx
from ..base import BaseParameter

LAKEFRONT_KEYWORDS = {"lakefront", "lake shore", "riverwalk", "river walk", "chicago river"}


class LakefrontAccess(BaseParameter):
    key = "lakefront_access"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key} (OSM tags)…")
        count = 0
        for u, v, k, data in G.edges(keys=True, data=True):
            name = str(data.get("name", "")).lower()
            desc = str(data.get("description", "")).lower()
            ref = str(data.get("ref", "")).lower()
            combined = f"{name} {desc} {ref}"

            highway = str(data.get("highway", "")).lower()
            is_path = highway in ("path", "footway", "pedestrian", "cycleway")

            if any(kw in combined for kw in LAKEFRONT_KEYWORDS):
                score = 1.0
                count += 1
            elif is_path and "lake" in combined:
                score = 0.7
                count += 1
            else:
                score = 0.0

            G[u][v][k][f"param_{self.key}"] = score

        print(f"    {count} lakefront/riverwalk segments tagged")
