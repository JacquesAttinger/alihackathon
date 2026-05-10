"""Score 1.0 for alleys and narrow service passages, 0.0 elsewhere."""
import networkx as nx
from ..base import BaseParameter


class AlleyAvoidance(BaseParameter):
    key = "alley_avoidance"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key} (OSM)…")
        count = 0
        for u, v, k, data in G.edges(keys=True, data=True):
            hw = str(data.get("highway", "")).lower()
            name = str(data.get("name", "")).lower()
            is_alley = hw == "alley" or "alley" in name or (hw == "service" and not data.get("name"))
            score = 1.0 if is_alley else 0.0
            if is_alley:
                count += 1
            G[u][v][k][f"param_{self.key}"] = score
        print(f"    {count} alley segments tagged")
