"""Shared spatial indexing utilities used by all parameter scorers."""
import math
from abc import ABC
from typing import Any
import networkx as nx

CELL_DEG = 0.002  # ~200m grid cells


def build_point_grid(points: list[tuple[float, float]], values: list[float] | None = None) -> dict[tuple[int, int], float]:
    grid: dict[tuple[int, int], float] = {}
    vals = values if values is not None else [1.0] * len(points)
    for (lat, lng), val in zip(points, vals):
        key = (int(lat / CELL_DEG), int(lng / CELL_DEG))
        grid[key] = grid.get(key, 0.0) + val
    return grid


def grid_score_at(lat: float, lng: float, grid: dict, radius_cells: int = 1) -> float:
    row, col = int(lat / CELL_DEG), int(lng / CELL_DEG)
    return sum(
        grid.get((row + dr, col + dc), 0.0)
        for dr in range(-radius_cells, radius_cells + 1)
        for dc in range(-radius_cells, radius_cells + 1)
    )


def edge_midpoint(G: nx.MultiDiGraph, u: Any, v: Any) -> tuple[float, float]:
    return (G.nodes[u]["y"] + G.nodes[v]["y"]) / 2, (G.nodes[u]["x"] + G.nodes[v]["x"]) / 2


class BaseParameter(ABC):
    key: str

    def _write_all(self, G: nx.MultiDiGraph, value: float) -> None:
        for u, v, k in G.edges(keys=True):
            G[u][v][k][f"param_{self.key}"] = value

    def _write_from_grid(self, G: nx.MultiDiGraph, grid: dict, max_val: float) -> None:
        for u, v, k in G.edges(keys=True):
            lat, lng = edge_midpoint(G, u, v)
            raw = grid_score_at(lat, lng, grid)
            G[u][v][k][f"param_{self.key}"] = min(raw / max_val, 1.0) if max_val > 0 else 0.0
