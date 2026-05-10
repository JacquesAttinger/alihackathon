import os
import pickle
import math
import networkx as nx
import osmnx as ox
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from parks import load_parks, best_park_node

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="SafeWalk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

G: nx.MultiDiGraph | None = None
PARKS: list[dict] = []
GRAPH_CACHE_PATH = os.path.join(os.path.dirname(__file__), "cache", "chicago_graph.pkl")


@app.on_event("startup")
async def startup():
    global G, PARKS

    PARKS = load_parks()

    if os.path.exists(GRAPH_CACHE_PATH):
        print("Loading graph from cache…")
        with open(GRAPH_CACHE_PATH, "rb") as f:
            G = pickle.load(f)
        print("Ready.")
        return

    print("Loading Chicago street graph (first run — will be cached after this)…")
    G = ox.graph_from_place("Chicago, Illinois, USA", network_type="walk", retain_all=False)
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)

    os.makedirs(os.path.dirname(GRAPH_CACHE_PATH), exist_ok=True)
    print("Saving graph to cache…")
    with open(GRAPH_CACHE_PATH, "wb") as f:
        pickle.dump(G, f)
    print("Ready.")


# ── Route ─────────────────────────────────────────────────────────────────────

class RouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float


@app.post("/api/route")
async def get_route(req: RouteRequest):
    if G is None:
        raise HTTPException(503, "Graph not loaded yet — retry in a moment")

    try:
        start_node = ox.distance.nearest_nodes(G, req.start_lng, req.start_lat)
        end_node   = ox.distance.nearest_nodes(G, req.end_lng,   req.end_lat)
    except Exception as e:
        raise HTTPException(400, f"Could not find nearest nodes: {e}")

    # Find the park that adds the least detour
    park_node, park_name = best_park_node(
        G, PARKS,
        req.start_lat, req.start_lng,
        req.end_lat,   req.end_lng,
    )

    try:
        if park_node and park_node != start_node and park_node != end_node:
            leg1 = nx.shortest_path(G, start_node, park_node, weight="length")
            leg2 = nx.shortest_path(G, park_node,  end_node,  weight="length")
            # Avoid duplicating the park node at the join
            path = leg1 + leg2[1:]
        else:
            park_name = None
            path = nx.shortest_path(G, start_node, end_node, weight="length")
    except nx.NetworkXNoPath:
        raise HTTPException(400, "No walkable route found between these points")

    # Filter out any nodes with non-finite coordinates (rare OSM data issues)
    coords = [
        [G.nodes[n]["x"], G.nodes[n]["y"]]
        for n in path
        if math.isfinite(G.nodes[n]["x"]) and math.isfinite(G.nodes[n]["y"])
    ]

    total_length = 0.0
    for u, v in zip(path[:-1], path[1:]):
        length = min(G[u][v][k].get("length", 50) for k in G[u][v])
        if math.isfinite(length):
            total_length += length
        else:
            total_length += 50  # fallback for bad edges
    walking_minutes = round(total_length / 80)

    return {
        "route": {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {},
        },
        "park_name": park_name,
        "walking_minutes": walking_minutes,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "graph_loaded": G is not None, "parks_loaded": len(PARKS)}
