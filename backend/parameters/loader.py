"""
ParameterLoader: loads all parameters into the street graph in dependency order.
Tier 1-3 run independently; Tier 4 composites run last.
"""
import networkx as nx
from .base import BaseParameter

# Tier 1
from .tier1.violent_crime import ViolentCrime
from .tier1.property_crime import PropertyCrime
from .tier1.street_lights import StreetLights
from .tier1.park_proximity import ParkProximity
from .tier1.tree_canopy import TreeCanopy
from .tier1.transit_proximity import TransitProximity
from .tier1.blight_311 import Blight311
from .tier1.public_art import PublicArt
from .tier1.landmarks import Landmarks
from .tier1.lakefront_access import LakefrontAccess

# Tier 2
from .tier2.restaurant_density import RestaurantDensity
from .tier2.nightlife_density import NightlifeDensity
from .tier2.coffee_shop_density import CoffeeShopDensity
from .tier2.open_businesses import OpenBusinesses
from .tier2.foot_traffic import FootTraffic

# Tier 3
from .tier3.road_type import RoadType
from .tier3.sidewalk_quality import SidewalkQuality
from .tier3.dead_zones import DeadZones
from .tier3.crossing_safety import CrossingSafety
from .tier3.building_density import BuildingDensity
from .tier3.alley_avoidance import AlleyAvoidance
from .tier3.school_proximity import SchoolProximity
from .tier3.playground_proximity import PlaygroundProximity
from .tier3.place_of_worship import PlaceOfWorship

# Tier 4 (composites — must run after 1-3)
from .tier4.composites import (
    ScenicQuality, Quietness, RomanticVibe, Liveliness,
    FamilyFriendliness, LateNightSafety, TouristInterest,
    DogFriendly, ExerciseFitness,
)

TIER_1_3: list[BaseParameter] = [
    ViolentCrime(), PropertyCrime(), StreetLights(), ParkProximity(),
    TreeCanopy(), TransitProximity(), Blight311(), PublicArt(),
    Landmarks(), LakefrontAccess(),
    RestaurantDensity(), NightlifeDensity(), CoffeeShopDensity(),
    OpenBusinesses(), FootTraffic(),
    RoadType(), SidewalkQuality(), DeadZones(), CrossingSafety(),
    BuildingDensity(), AlleyAvoidance(), SchoolProximity(),
    PlaygroundProximity(), PlaceOfWorship(),
]

TIER_4: list[BaseParameter] = [
    ScenicQuality(), Quietness(), RomanticVibe(), Liveliness(),
    FamilyFriendliness(), LateNightSafety(), TouristInterest(),
    DogFriendly(), ExerciseFitness(),
]


class ParameterLoader:
    def load_all(self, G: nx.MultiDiGraph) -> None:
        print("Loading Tier 1–3 parameters…")
        for param in TIER_1_3:
            param.load(G)

        print("Computing Tier 4 composites…")
        for param in TIER_4:
            param.load(G)

        print(f"All {len(TIER_1_3) + len(TIER_4)} parameters loaded.")
