"""Industrial areas, rail yards, vacant lots — existing logic ported to new system."""
import networkx as nx
from ..base import BaseParameter

DEAD_LANDUSE = {"industrial", "railway", "landfill", "construction", "brownfield"}
DEAD_LEISURE = {"park"}  # parks at night; scored separately from park_proximity
DEAD_HIGHWAY = {"service", "track"}


class DeadZones(BaseParameter):
    key = "dead_zones"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Loading {self.key} (OSM)…")
        count = 0
        for u, v, k, data in G.edges(keys=True, data=True):
            landuse = str(data.get("landuse", "")).lower()
            leisure = str(data.get("leisure", "")).lower()
            hw = str(data.get("highway", "")).lower()

            is_dead = (
                any(d in landuse for d in DEAD_LANDUSE)
                or (any(d in leisure for d in DEAD_LEISURE) and "playground" not in leisure)
                or hw in DEAD_HIGHWAY
            )
            score = 1.0 if is_dead else 0.0
            if is_dead:
                count += 1
            G[u][v][k][f"param_{self.key}"] = score

        print(f"    {count} dead-zone segments tagged")
