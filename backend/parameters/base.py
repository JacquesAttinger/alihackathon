"""Abstract base class for all parameter scorers."""

import math
from abc import ABC, abstractmethod
from typing import Any
import networkx as nx


CELL_DEG = 0.002  # ~200m grid cells


def build_point_grid(points: list[tuple[float, float]], values: list[float] | None = None) -> dict[tuple[int, int], float]:
    """Bucket (lat, lng) points into a grid. Returns grid_key -> cumulative value."""
    grid: dict[tuple[int, int], float] = {}
    vals = values if values is not None else [1.0] * len(points)
    for (lat, lng), val in zip(points, vals):
        key = (int(lat / CELL_DEG), int(lng / CELL_DEG))
        grid[key] = grid.get(key, 0.0) + val
    return grid


def grid_score_at(lat: float, lng: float, grid: dict[tuple[int, int], float], radius_cells: int = 1) -> float:
    """Sum grid values within radius_cells of (lat, lng)."""
    row = int(lat / CELL_DEG)
    col = int(lng / CELL_DEG)
    total = 0.0
    for dr in range(-radius_cells, radius_cells + 1):
        for dc in range(-radius_cells, radius_cells + 1):
            total += grid.get((row + dr, col + dc), 0.0)
    return total


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((lat2 - lat1) * math.pi / 360) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin((lng2 - lng1) * math.pi / 360) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def edge_midpoint(G: nx.MultiDiGraph, u: Any, v: Any) -> tuple[float, float]:
    """Return (lat, lng) midpoint of a graph edge."""
    return (
        (G.nodes[u]["y"] + G.nodes[v]["y"]) / 2,
        (G.nodes[u]["x"] + G.nodes[v]["x"]) / 2,
    )


def normalize(value: float, max_val: float) -> float:
    """Clamp value to [0, max_val] then scale to 0.0–1.0."""
    return min(value / max_val, 1.0) if max_val > 0 else 0.0


class BaseParameter(ABC):
    key: str

    def load(self, G: nx.MultiDiGraph) -> None:
        """
        Load external data and write a per-edge score into
        G[u][v][k][f'param_{self.key}'] for all edges.
        Score is always 0.0–1.0.
        Default impl writes 0.0 everywhere (no data).
        """
        self._write_all(G, 0.0)

    def _write_all(self, G: nx.MultiDiGraph, default: float) -> None:
        for u, v, k in G.edges(keys=True):
            G[u][v][k][f"param_{self.key}"] = default

    def _write_from_grid(self, G: nx.MultiDiGraph, grid: dict, max_val: float) -> None:
        for u, v, k in G.edges(keys=True):
            lat, lng = edge_midpoint(G, u, v)
            raw = grid_score_at(lat, lng, grid)
            G[u][v][k][f"param_{self.key}"] = normalize(raw, max_val)
