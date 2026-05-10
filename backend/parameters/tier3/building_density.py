"""
Building density as an "eyes on the street" proxy.
Uses the OSM building tag on adjacent areas. Higher density = more eyes = safer feel.
Proxy: road type is a reasonable stand-in (dense urban streets = more buildings).
"""
import networkx as nx
from ..base import BaseParameter

HIGH_DENSITY = {"primary", "secondary", "tertiary", "pedestrian"}
MED_DENSITY = {"residential", "living_street", "unclassified"}


class BuildingDensity(BaseParameter):
    key = "building_density"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key} (OSM proxy)…")
        for u, v, k, data in G.edges(keys=True, data=True):
            hw = str(data.get("highway", "")).lower()
            if any(t in hw for t in HIGH_DENSITY):
                score = 0.9
            elif any(t in hw for t in MED_DENSITY):
                score = 0.6
            else:
                score = 0.2
            G[u][v][k][f"param_{self.key}"] = score
