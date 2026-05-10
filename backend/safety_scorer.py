"""
Attaches safety weights to every edge in the street graph.
Higher weight = more dangerous = avoided by the router.
"""
import requests
import math

CHICAGO_CRIME_URL = (
    "https://data.cityofchicago.org/resource/ijzp-q8t2.json"
    "?$limit=50000"
    "&$where=year>=2023"
    "&$select=latitude,longitude,primary_type"
)

VIOLENT_TYPES = {
    "ASSAULT", "BATTERY", "ROBBERY", "HOMICIDE",
    "CRIM SEXUAL ASSAULT", "KIDNAPPING",
}


def fetch_crime_points() -> list[tuple[float, float, bool]]:
    """Returns list of (lat, lng, is_violent) for recent Chicago crimes."""
    print("Fetching Chicago crime data…")
    try:
        resp = requests.get(CHICAGO_CRIME_URL, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
        points = []
        for r in rows:
            try:
                lat = float(r["latitude"])
                lng = float(r["longitude"])
                violent = r.get("primary_type", "").upper() in VIOLENT_TYPES
                points.append((lat, lng, violent))
            except (KeyError, ValueError, TypeError):
                continue
        print(f"  Loaded {len(points)} crime incidents")
        return points
    except Exception as e:
        print(f"  Crime fetch failed: {e} — using empty dataset")
        return []


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_crime_grid(points: list[tuple[float, float, bool]], cell_deg: float = 0.002) -> dict[tuple[int, int], float]:
    """Bucket crimes into a coarse grid; returns grid_key -> danger_score."""
    grid: dict[tuple[int, int], float] = {}
    for lat, lng, violent in points:
        key = (int(lat / cell_deg), int(lng / cell_deg))
        grid[key] = grid.get(key, 0.0) + (2.0 if violent else 1.0)
    return grid


def crime_penalty(lat: float, lng: float, grid: dict, cell_deg: float = 0.002) -> float:
    """Returns a multiplier 1.0–3.0 based on nearby crime density."""
    key = (int(lat / cell_deg), int(lng / cell_deg))
    score = 0.0
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            score += grid.get((key[0] + di, key[1] + dj), 0.0)
    # Normalize: cap at 30 incidents → penalty 3.0
    return 1.0 + min(score / 15.0, 2.0)


def road_lighting_multiplier(highway_tag: str) -> float:
    """Proxy: major roads assumed lit, alleys / paths not."""
    well_lit = {"primary", "secondary", "tertiary", "residential"}
    poor_lit = {"service", "alley", "path", "track", "unclassified"}
    tag = str(highway_tag).lower() if highway_tag else ""
    if any(t in tag for t in well_lit):
        return 1.0
    if any(t in tag for t in poor_lit):
        return 1.8
    return 1.2


def is_dead_zone(tags: dict) -> bool:
    """True for industrial areas, large parks, and vacant lots."""
    landuse = str(tags.get("landuse", "")).lower()
    leisure = str(tags.get("leisure", "")).lower()
    dead = {"industrial", "railway", "landfill", "construction"}
    if any(d in landuse for d in dead):
        return True
    if "park" in leisure and "playground" not in leisure:
        return True
    return False


def apply_safety_weights(G, crime_grid: dict) -> None:
    """Mutates graph edges in place, adding 'safety_cost' attribute."""
    for u, v, data in G.edges(data=True):
        length = data.get("length", 50)

        # midpoint of edge
        u_data = G.nodes[u]
        v_data = G.nodes[v]
        mid_lat = (u_data["y"] + v_data["y"]) / 2
        mid_lng = (u_data["x"] + v_data["x"]) / 2

        crime_mult = crime_penalty(mid_lat, mid_lng, crime_grid)
        light_mult = road_lighting_multiplier(data.get("highway", ""))
        dead_mult = 5.0 if is_dead_zone(data) else 1.0

        data["safety_cost"] = length * crime_mult * light_mult * dead_mult
