"""
Central registry of all route optimization parameters.
This is the contract between the routing algorithm and the LLM/UI layer.

Each parameter key is a snake_case string. The LLM outputs a dict of
{ key: weight } where weight is 0.0–1.0 (how much the user cares).

direction:
  "avoid"  → higher edge score = worse (e.g. crime: score 1.0 = very dangerous)
  "prefer" → higher edge score = better (e.g. park_proximity: score 1.0 = next to a park)
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterDef:
    key: str
    name: str
    description: str
    tier: int          # 1=city data, 2=API, 3=OSM, 4=composite
    category: str      # safety | aesthetics | social | practical
    direction: str     # "avoid" | "prefer"
    requires_key: str | None = None   # API key name needed, or None


PARAMETER_REGISTRY: dict[str, ParameterDef] = {p.key: p for p in [

    # ── Tier 1: Chicago open data ────────────────────────────────────────────

    ParameterDef(
        key="violent_crime",
        name="Violent Crime",
        description="Density of assaults, robbery, homicide nearby",
        tier=1, category="safety", direction="avoid",
    ),
    ParameterDef(
        key="property_crime",
        name="Property Crime",
        description="Density of theft, burglary, vandalism nearby",
        tier=1, category="safety", direction="avoid",
    ),
    ParameterDef(
        key="street_lights",
        name="Street Lighting",
        description="Presence of street lights on this segment",
        tier=1, category="safety", direction="prefer",
    ),
    ParameterDef(
        key="park_proximity",
        name="Park Proximity",
        description="Closeness to Chicago parks and green space",
        tier=1, category="aesthetics", direction="prefer",
    ),
    ParameterDef(
        key="tree_canopy",
        name="Tree Canopy",
        description="Shade and greenery from Chicago's tree inventory",
        tier=1, category="aesthetics", direction="prefer",
    ),
    ParameterDef(
        key="transit_proximity",
        name="Transit Access",
        description="Closeness to CTA L stops and bus stops",
        tier=1, category="practical", direction="prefer",
    ),
    ParameterDef(
        key="blight_311",
        name="Neighborhood Blight",
        description="311 complaints for graffiti, dumping, abandoned buildings",
        tier=1, category="safety", direction="avoid",
    ),
    ParameterDef(
        key="public_art",
        name="Public Art",
        description="Murals, sculptures, and installations along the route",
        tier=1, category="aesthetics", direction="prefer",
    ),
    ParameterDef(
        key="landmarks",
        name="Historic Landmarks",
        description="Chicago landmark buildings and architectural interest",
        tier=1, category="aesthetics", direction="prefer",
    ),
    ParameterDef(
        key="lakefront_access",
        name="Lakefront / Riverwalk",
        description="Route runs along Lake Michigan or the Chicago Riverwalk",
        tier=1, category="aesthetics", direction="prefer",
    ),

    # ── Tier 2: External APIs ────────────────────────────────────────────────

    ParameterDef(
        key="restaurant_density",
        name="Restaurant Density",
        description="Number of restaurants and eateries nearby",
        tier=2, category="social", direction="prefer",
        requires_key="GOOGLE_PLACES_API_KEY",
    ),
    ParameterDef(
        key="nightlife_density",
        name="Nightlife Density",
        description="Bars, clubs, and late-night venues nearby",
        tier=2, category="social", direction="prefer",
        requires_key="GOOGLE_PLACES_API_KEY",
    ),
    ParameterDef(
        key="coffee_shop_density",
        name="Coffee Shop Density",
        description="Cafes and coffee shops along the route",
        tier=2, category="social", direction="prefer",
        requires_key="GOOGLE_PLACES_API_KEY",
    ),
    ParameterDef(
        key="open_businesses",
        name="Open Businesses",
        description="Businesses currently open (eyes on the street)",
        tier=2, category="safety", direction="prefer",
        requires_key="GOOGLE_PLACES_API_KEY",
    ),
    ParameterDef(
        key="foot_traffic",
        name="Foot Traffic",
        description="How busy and populated the street currently is",
        tier=2, category="social", direction="prefer",
        requires_key="FOURSQUARE_API_KEY",
    ),

    # ── Tier 3: OSM-derived ──────────────────────────────────────────────────

    ParameterDef(
        key="road_type",
        name="Road Type",
        description="Prefer main roads over alleys and service roads",
        tier=3, category="safety", direction="prefer",
    ),
    ParameterDef(
        key="sidewalk_quality",
        name="Sidewalk Quality",
        description="Whether a proper sidewalk exists on this segment",
        tier=3, category="practical", direction="prefer",
    ),
    ParameterDef(
        key="dead_zones",
        name="Dead Zone Avoidance",
        description="Avoid industrial areas, rail yards, and vacant zones",
        tier=3, category="safety", direction="avoid",
    ),
    ParameterDef(
        key="crossing_safety",
        name="Crossing Safety",
        description="Prefer signalized crosswalks over unmarked crossings",
        tier=3, category="safety", direction="prefer",
    ),
    ParameterDef(
        key="building_density",
        name="Building Density",
        description="Urban streets with buildings on both sides (eyes on street)",
        tier=3, category="safety", direction="prefer",
    ),
    ParameterDef(
        key="alley_avoidance",
        name="Alley Avoidance",
        description="Avoid alleys and narrow service passages",
        tier=3, category="safety", direction="avoid",
    ),
    ParameterDef(
        key="school_proximity",
        name="School Proximity",
        description="Route passes near schools (safe, family-friendly zones)",
        tier=3, category="social", direction="prefer",
    ),
    ParameterDef(
        key="playground_proximity",
        name="Playground Proximity",
        description="Closeness to playgrounds and children's areas",
        tier=3, category="social", direction="prefer",
    ),
    ParameterDef(
        key="place_of_worship",
        name="Community Anchors",
        description="Churches, mosques, temples — community gathering points",
        tier=3, category="social", direction="prefer",
    ),

    # ── Tier 4: Composite proxies ────────────────────────────────────────────

    ParameterDef(
        key="scenic_quality",
        name="Scenic Quality",
        description="Overall beauty: water, trees, parks, landmarks",
        tier=4, category="aesthetics", direction="prefer",
    ),
    ParameterDef(
        key="quietness",
        name="Quietness",
        description="Peaceful, low-traffic, low-noise streets",
        tier=4, category="aesthetics", direction="prefer",
    ),
    ParameterDef(
        key="romantic_vibe",
        name="Romantic Vibe",
        description="Lit, beautiful, restaurant-lined, near water",
        tier=4, category="aesthetics", direction="prefer",
    ),
    ParameterDef(
        key="liveliness",
        name="Liveliness",
        description="Busy, energetic streets with lots happening",
        tier=4, category="social", direction="prefer",
    ),
    ParameterDef(
        key="family_friendliness",
        name="Family Friendly",
        description="Safe, calm, near parks and schools",
        tier=4, category="social", direction="prefer",
    ),
    ParameterDef(
        key="late_night_safety",
        name="Late Night Safety",
        description="Optimized specifically for walking after dark",
        tier=4, category="safety", direction="prefer",
    ),
    ParameterDef(
        key="tourist_interest",
        name="Tourist Interest",
        description="Passes landmarks, public art, riverwalk, architecture",
        tier=4, category="aesthetics", direction="prefer",
    ),
    ParameterDef(
        key="dog_friendly",
        name="Dog Friendly",
        description="Parks, green space, wide sidewalks, low traffic",
        tier=4, category="social", direction="prefer",
    ),
    ParameterDef(
        key="exercise_fitness",
        name="Exercise / Fitness",
        description="Direct, flat, wide paths good for a brisk walk",
        tier=4, category="practical", direction="prefer",
    ),
]}
