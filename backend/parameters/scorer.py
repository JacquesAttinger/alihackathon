"""
Converts a module weight vector into a per-edge routing cost.

For "prefer" parameters (like scenic_quality):
  cost = length / (1 + weight × score)
  → a fully-scenic edge with weight=1.0 costs half as much as a bare edge
  → the router treats scenic streets as effectively shorter, so it prefers them

For "avoid" parameters (none active yet):
  cost = length × (1 + weight × score × 4)
"""
import networkx as nx
from .registry import PARAMETER_REGISTRY


def compute_edge_cost(data: dict, weights: dict[str, float]) -> float:
    cost = data.get("length", 50.0)
    for key, weight in weights.items():
        if weight <= 0 or key not in PARAMETER_REGISTRY:
            continue
        score = data.get(f"param_{key}", 0.0)
        if PARAMETER_REGISTRY[key].direction == "prefer":
            cost /= (1.0 + weight * score)
        else:
            cost *= (1.0 + weight * score * 4.0)
    return max(cost, 0.1)


def apply_weights(G: nx.MultiDiGraph, weights: dict[str, float]) -> None:
    for u, v, k, data in G.edges(keys=True, data=True):
        G[u][v][k]["module_cost"] = compute_edge_cost(data, weights)


def score_route(G: nx.MultiDiGraph, path: list, weights: dict[str, float]) -> dict:
    totals: dict[str, float] = {}
    total_length = 0.0

    for u, v in zip(path[:-1], path[1:]):
        data = min(G[u][v].values(), key=lambda d: d.get("module_cost", 9e9))
        total_length += data.get("length", 50.0)
        for key in weights:
            totals[key] = totals.get(key, 0.0) + data.get(f"param_{key}", 0.0)

    n = max(len(path) - 1, 1)
    averages = {k: v / n for k, v in totals.items()}
    walking_minutes = round(total_length / 80)

    # Overall score: average of all active param scores (0–100)
    scores = []
    for key, avg in averages.items():
        if key in PARAMETER_REGISTRY:
            scores.append(avg if PARAMETER_REGISTRY[key].direction == "prefer" else 1.0 - avg)
    overall = round((sum(scores) / len(scores)) * 100) if scores else 50

    return {
        "overall_score": overall,
        "walking_minutes": walking_minutes,
        "param_scores": averages,
    }
