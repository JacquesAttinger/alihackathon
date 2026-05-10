"""
Converts a module weight vector into a per-edge routing cost.

Edge cost formula:
  cost = length
       × Π (1 + w × score × AVOID_SCALE)   for "avoid" params
       / Π (1 + w × score × PREFER_SCALE)  for "prefer" params

AVOID_SCALE=4  → a fully-weighted, fully-bad edge costs up to 5× longer
PREFER_SCALE=1 → a fully-weighted, fully-good edge costs down to ½ as long
"""

import networkx as nx
from .registry import PARAMETER_REGISTRY

AVOID_SCALE = 4.0
PREFER_SCALE = 1.0


def compute_edge_cost(u, v, data: dict, weights: dict[str, float]) -> float:
    length = data.get("length", 50.0)
    cost = length

    for key, weight in weights.items():
        if weight <= 0 or key not in PARAMETER_REGISTRY:
            continue
        param_def = PARAMETER_REGISTRY[key]
        score = data.get(f"param_{key}", 0.0)

        if param_def.direction == "avoid":
            cost *= 1.0 + weight * score * AVOID_SCALE
        else:
            cost /= 1.0 + weight * score * PREFER_SCALE

    return max(cost, 0.1)


def apply_module_weights(G: nx.MultiDiGraph, weights: dict[str, float]) -> None:
    """Write 'module_cost' onto every edge for use as Dijkstra weight."""
    for u, v, k, data in G.edges(keys=True, data=True):
        G[u][v][k]["module_cost"] = compute_edge_cost(u, v, data, weights)


def score_route(G: nx.MultiDiGraph, path: list, weights: dict[str, float]) -> dict:
    """Compute per-parameter summary scores for display in the UI."""
    param_totals: dict[str, float] = {}
    total_length = 0.0
    edge_count = 0

    for u, v in zip(path[:-1], path[1:]):
        data = min(G[u][v].values(), key=lambda d: d.get("module_cost", 9e9))
        total_length += data.get("length", 50.0)
        edge_count += 1
        for key in weights:
            val = data.get(f"param_{key}", 0.0)
            param_totals[key] = param_totals.get(key, 0.0) + val

    averages = {k: v / max(edge_count, 1) for k, v in param_totals.items()}
    walking_minutes = round(total_length / 80)

    # Overall score: invert avoid-params, keep prefer-params, average
    scores = []
    for key, avg in averages.items():
        if key not in PARAMETER_REGISTRY:
            continue
        if PARAMETER_REGISTRY[key].direction == "avoid":
            scores.append(1.0 - avg)
        else:
            scores.append(avg)

    overall = round((sum(scores) / max(len(scores), 1)) * 100) if scores else 50

    return {
        "overall_score": overall,
        "walking_minutes": walking_minutes,
        "param_scores": averages,
    }
