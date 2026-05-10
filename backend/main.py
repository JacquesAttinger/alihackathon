import os
import json
import networkx as nx
import osmnx as ox
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from parameters import ParameterLoader, Module, PARAMETER_REGISTRY
from parameters.scorer import apply_module_weights, score_route

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="SafeWalk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

G: nx.MultiDiGraph | None = None

# In-memory module store (replace with a database later)
_modules: dict[str, Module] = {}

# Default "safe walk" module used when no module is specified
DEFAULT_WEIGHTS = {
    "violent_crime": 0.9,
    "property_crime": 0.5,
    "street_lights": 0.8,
    "dead_zones": 0.9,
    "alley_avoidance": 0.7,
    "blight_311": 0.4,
    "road_type": 0.5,
    "sidewalk_quality": 0.6,
    "open_businesses": 0.5,
}


@app.on_event("startup")
async def startup():
    global G
    print("Loading Chicago street graph (this takes ~60 s the first time)…")
    G = ox.graph_from_place("Chicago, Illinois, USA", network_type="walk", retain_all=False)
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)

    loader = ParameterLoader()
    loader.load_all(G)

    # Pre-compute default module costs
    apply_module_weights(G, DEFAULT_WEIGHTS)
    print("Ready.")


# ── Route endpoint ────────────────────────────────────────────────────────────

class RouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    module_id: str | None = None   # if None, uses DEFAULT_WEIGHTS
    weights: dict[str, float] | None = None  # inline weights (overrides module)


@app.post("/api/route")
async def get_route(req: RouteRequest):
    if G is None:
        raise HTTPException(503, "Graph not loaded yet — retry in a moment")

    # Resolve weights
    if req.weights:
        weights = req.weights
    elif req.module_id and req.module_id in _modules:
        weights = _modules[req.module_id].weights
    else:
        weights = DEFAULT_WEIGHTS

    apply_module_weights(G, weights)

    try:
        start_node = ox.distance.nearest_nodes(G, req.start_lng, req.start_lat)
        end_node = ox.distance.nearest_nodes(G, req.end_lng, req.end_lat)
    except Exception as e:
        raise HTTPException(400, f"Could not find nearest nodes: {e}")

    try:
        path = nx.shortest_path(G, start_node, end_node, weight="module_cost")
    except nx.NetworkXNoPath:
        raise HTTPException(400, "No walkable route found between these points")

    coords = [[G.nodes[n]["x"], G.nodes[n]["y"]] for n in path]
    metrics = score_route(G, path, weights)

    return {
        "route": {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {},
        },
        **metrics,
    }


# ── Module endpoints ──────────────────────────────────────────────────────────

class ModuleCreate(BaseModel):
    name: str
    prompt: str
    weights: dict[str, float]


@app.post("/api/modules")
async def create_module(body: ModuleCreate):
    # Validate keys against registry
    invalid = [k for k in body.weights if k not in PARAMETER_REGISTRY]
    if invalid:
        raise HTTPException(400, f"Unknown parameter keys: {invalid}")
    module = Module(name=body.name, prompt=body.prompt, weights=body.weights)
    _modules[module.id] = module
    return module.to_dict()


@app.get("/api/modules")
async def list_modules():
    return [m.to_dict() for m in _modules.values()]


@app.get("/api/modules/{module_id}")
async def get_module(module_id: str):
    if module_id not in _modules:
        raise HTTPException(404, "Module not found")
    return _modules[module_id].to_dict()


@app.delete("/api/modules/{module_id}")
async def delete_module(module_id: str):
    if module_id not in _modules:
        raise HTTPException(404, "Module not found")
    del _modules[module_id]
    return {"deleted": module_id}


# ── Parameter registry endpoint (for the UI/LLM) ─────────────────────────────

@app.get("/api/parameters")
async def get_parameters():
    return [
        {
            "key": p.key,
            "name": p.name,
            "description": p.description,
            "tier": p.tier,
            "category": p.category,
            "direction": p.direction,
        }
        for p in PARAMETER_REGISTRY.values()
    ]


@app.get("/health")
async def health():
    return {"status": "ok", "graph_loaded": G is not None}
