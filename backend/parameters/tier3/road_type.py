"""Prefer main roads over service roads. Score based on OSM highway tag."""
import networkx as nx
from ..base import BaseParameter

SCORES = {
    "primary": 0.95, "primary_link": 0.9,
    "secondary": 0.9, "secondary_link": 0.85,
    "tertiary": 0.85, "tertiary_link": 0.8,
    "residential": 0.75,
    "living_street": 0.7,
    "pedestrian": 0.9,
    "footway": 0.8,
    "path": 0.6,
    "unclassified": 0.5,
    "service": 0.3,
    "alley": 0.1,
    "track": 0.2,
}


class RoadType(BaseParameter):
    key = "road_type"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key} (OSM)…")
        for u, v, k, data in G.edges(keys=True, data=True):
            hw = str(data.get("highway", "")).lower()
            score = next((v for t, v in SCORES.items() if t in hw), 0.4)
            G[u][v][k][f"param_{self.key}"] = score
