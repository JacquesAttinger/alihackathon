import os
import math
import networkx as nx
import osmnx as ox
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from safety_scorer import fetch_crime_points, build_crime_grid, apply_safety_weights

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="SafeWalk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

G: nx.MultiDiGraph | None = None


@app.on_event("startup")
async def startup():
    global G
    print("Loading Chicago street graph (this takes ~60 seconds the first time)…")
    # OSMnx caches the graph locally after the first download
    G = ox.graph_from_place("Chicago, Illinois, USA", network_type="walk", retain_all=False)
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)

    print("Applying safety weights…")
    crime_points = fetch_crime_points()
    crime_grid = build_crime_grid(crime_points)
    apply_safety_weights(G, crime_grid)
    print("Ready.")


class RouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float


def _score_route(G, path: list) -> dict:
    """Compute aggregate safety metrics for display."""
    crime_costs, light_costs, dead_count = [], [], 0
    total_length = 0

    for u, v in zip(path[:-1], path[1:]):
        data = min(G[u][v].values(), key=lambda d: d.get("safety_cost", 9e9))
        length = data.get("length", 50)
        total_length += length

        crime_mult = data.get("safety_cost", length) / max(length, 1)
        crime_costs.append(crime_mult)

        hw = str(data.get("highway", "")).lower()
        if any(t in hw for t in ("primary", "secondary", "tertiary", "residential")):
            light_costs.append(1.0)
        else:
            light_costs.append(1.5)

        if data.get("safety_cost", 0) > length * 4:
            dead_count += 1

    avg_crime = sum(crime_costs) / max(len(crime_costs), 1)
    avg_light = sum(light_costs) / max(len(light_costs), 1)

    # Convert penalties to a 0–100 score (lower penalty = higher score)
    raw_danger = (avg_crime - 1) / 2 * 50 + (avg_light - 1) / 0.8 * 30 + dead_count * 10
    safety_score = max(10, min(100, round(100 - raw_danger)))

    walking_minutes = round(total_length / 80)  # ~80 m/min walking pace

    crime_label = (
        "Low crime area" if avg_crime < 1.4 else
        "Moderate crime history" if avg_crime < 2.0 else
        "Higher crime — stay alert"
    )
    light_label = (
        "Well-lit streets" if avg_light < 1.1 else
        "Mostly lit streets" if avg_light < 1.4 else
        "Some poorly lit segments"
    )
    dead_label = (
        "No dead zones on route" if dead_count == 0 else
        f"{dead_count} low-traffic segment{'s' if dead_count > 1 else ''} — stay aware"
    )

    return {
        "safety_score": safety_score,
        "walking_minutes": walking_minutes,
        "breakdown": {
            "lighting": light_label,
            "crime": crime_label,
            "businesses": "Business density data coming soon",
            "dead_zones": dead_label,
        },
    }


@app.post("/api/route")
async def get_route(req: RouteRequest):
    if G is None:
        raise HTTPException(503, "Graph not loaded yet — please wait a moment and retry")

    try:
        start_node = ox.distance.nearest_nodes(G, req.start_lng, req.start_lat)
        end_node = ox.distance.nearest_nodes(G, req.end_lng, req.end_lat)
    except Exception as e:
        raise HTTPException(400, f"Could not find nearest nodes: {e}")

    try:
        path = nx.shortest_path(G, start_node, end_node, weight="safety_cost")
    except nx.NetworkXNoPath:
        raise HTTPException(400, "No walkable route found between these points")

    coords = [[G.nodes[n]["x"], G.nodes[n]["y"]] for n in path]
    metrics = _score_route(G, path)

    return {
        "route": {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {},
        },
        **metrics,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "graph_loaded": G is not None}
