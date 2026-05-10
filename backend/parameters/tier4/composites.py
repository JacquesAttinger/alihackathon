"""
Tier 4 composite parameters. Each is a weighted average of Tier 1-3 scores.
Must be loaded AFTER all Tier 1-3 parameters have written their scores.
"""
import networkx as nx
from ..base import BaseParameter


def _weighted_avg(data: dict, components: list[tuple[str, float]]) -> float:
    total_weight = sum(w for _, w in components)
    if total_weight == 0:
        return 0.0
    score = sum(data.get(f"param_{key}", 0.0) * w for key, w in components)
    return score / total_weight


class ScenicQuality(BaseParameter):
    key = "scenic_quality"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Computing {self.key} (composite)…")
        components = [
            ("lakefront_access", 2.0),
            ("park_proximity", 1.5),
            ("tree_canopy", 1.0),
            ("public_art", 0.8),
            ("landmarks", 0.8),
        ]
        for u, v, k, data in G.edges(keys=True, data=True):
            G[u][v][k][f"param_{self.key}"] = _weighted_avg(data, components)


class Quietness(BaseParameter):
    key = "quietness"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Computing {self.key} (composite)…")
        for u, v, k, data in G.edges(keys=True, data=True):
            # Quiet = low traffic roads, away from bars, low foot traffic
            road = data.get("param_road_type", 0.5)
            bars = data.get("param_nightlife_density", 0.0)
            foot = data.get("param_foot_traffic", 0.0)
            alley = data.get("param_alley_avoidance", 0.0)
            # Residential streets are quiet; primary roads and bars are not
            quiet_road = 1.0 if road < 0.8 and road > 0.5 else (0.3 if road >= 0.9 else 0.5)
            score = (quiet_road * 0.5 + (1 - bars) * 0.3 + (1 - foot) * 0.2) * (1 - alley * 0.5)
            G[u][v][k][f"param_{self.key}"] = max(0.0, min(1.0, score))


class RomanticVibe(BaseParameter):
    key = "romantic_vibe"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Computing {self.key} (composite)…")
        components = [
            ("street_lights", 1.5),
            ("restaurant_density", 1.2),
            ("lakefront_access", 2.0),
            ("scenic_quality", 1.5),
            ("park_proximity", 0.8),
            ("tree_canopy", 0.8),
        ]
        avoid = [("violent_crime", 2.0), ("dead_zones", 1.5), ("alley_avoidance", 1.0)]
        for u, v, k, data in G.edges(keys=True, data=True):
            pos = _weighted_avg(data, components)
            neg = _weighted_avg(data, avoid)
            G[u][v][k][f"param_{self.key}"] = max(0.0, min(1.0, pos * (1 - neg * 0.6)))


class Liveliness(BaseParameter):
    key = "liveliness"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Computing {self.key} (composite)…")
        components = [
            ("restaurant_density", 1.0),
            ("nightlife_density", 1.2),
            ("coffee_shop_density", 0.8),
            ("foot_traffic", 1.5),
            ("open_businesses", 1.0),
            ("transit_proximity", 0.5),
        ]
        for u, v, k, data in G.edges(keys=True, data=True):
            G[u][v][k][f"param_{self.key}"] = _weighted_avg(data, components)


class FamilyFriendliness(BaseParameter):
    key = "family_friendliness"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Computing {self.key} (composite)…")
        pos = [
            ("park_proximity", 1.5),
            ("playground_proximity", 2.0),
            ("school_proximity", 1.0),
            ("sidewalk_quality", 1.0),
            ("street_lights", 1.0),
            ("tree_canopy", 0.5),
        ]
        neg = [("violent_crime", 2.0), ("nightlife_density", 1.0), ("alley_avoidance", 1.0)]
        for u, v, k, data in G.edges(keys=True, data=True):
            positive = _weighted_avg(data, pos)
            negative = _weighted_avg(data, neg)
            G[u][v][k][f"param_{self.key}"] = max(0.0, min(1.0, positive * (1 - negative * 0.7)))


class LateNightSafety(BaseParameter):
    key = "late_night_safety"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Computing {self.key} (composite)…")
        pos = [
            ("street_lights", 2.0),
            ("open_businesses", 1.5),
            ("foot_traffic", 1.0),
            ("road_type", 0.8),
        ]
        neg = [
            ("violent_crime", 2.5),
            ("dead_zones", 2.0),
            ("alley_avoidance", 1.5),
            ("blight_311", 1.0),
        ]
        for u, v, k, data in G.edges(keys=True, data=True):
            positive = _weighted_avg(data, pos)
            negative = _weighted_avg(data, neg)
            G[u][v][k][f"param_{self.key}"] = max(0.0, min(1.0, positive * (1 - negative * 0.8)))


class TouristInterest(BaseParameter):
    key = "tourist_interest"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Computing {self.key} (composite)…")
        components = [
            ("landmarks", 2.0),
            ("public_art", 1.5),
            ("lakefront_access", 2.0),
            ("scenic_quality", 1.0),
            ("restaurant_density", 0.8),
            ("transit_proximity", 0.5),
        ]
        for u, v, k, data in G.edges(keys=True, data=True):
            G[u][v][k][f"param_{self.key}"] = _weighted_avg(data, components)


class DogFriendly(BaseParameter):
    key = "dog_friendly"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Computing {self.key} (composite)…")
        components = [
            ("park_proximity", 2.0),
            ("tree_canopy", 1.0),
            ("sidewalk_quality", 1.5),
            ("playground_proximity", 0.5),
        ]
        neg = [("road_type", 0.5)]  # avoid very busy main roads
        for u, v, k, data in G.edges(keys=True, data=True):
            pos_score = _weighted_avg(data, components)
            road = data.get("param_road_type", 0.5)
            busy_road_penalty = max(0, road - 0.85) * 2  # penalize primary roads
            G[u][v][k][f"param_{self.key}"] = max(0.0, min(1.0, pos_score - busy_road_penalty))


class ExerciseFitness(BaseParameter):
    key = "exercise_fitness"

    def load(self, G: nx.MultiDiGraph) -> None:
        print(f"  Computing {self.key} (composite)…")
        for u, v, k, data in G.edges(keys=True, data=True):
            sidewalk = data.get("param_sidewalk_quality", 0.5)
            road = data.get("param_road_type", 0.5)
            lakefront = data.get("param_lakefront_access", 0.0)
            # Lakefront trail = perfect exercise route
            score = sidewalk * 0.4 + road * 0.3 + lakefront * 0.3
            G[u][v][k][f"param_{self.key}"] = min(1.0, score)
