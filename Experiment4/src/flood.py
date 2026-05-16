from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass
class FloodResult:
    water_level_m: float
    flooded_mask: np.ndarray
    depth_m: np.ndarray
    flooded_percentage: float
    flooded_area_m2: float
    flood_volume_m3: float
    max_depth_m: float
    connected_cells: int
    routing_enabled: bool


def default_source_mask(shape: tuple[int, int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    mask[:, 0] = True
    return mask


def _apply_connectivity(
    eligible: np.ndarray,
    source_mask: np.ndarray,
) -> tuple[np.ndarray, int]:
    rows, cols = eligible.shape
    flooded = np.zeros_like(eligible, dtype=bool)
    queue: deque[tuple[int, int]] = deque()

    starters = np.argwhere(eligible & source_mask)
    for r, c in starters:
        flooded[r, c] = True
        queue.append((int(r), int(c)))

    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr = r + dr
            nc = c + dc
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                continue
            if flooded[nr, nc] or not eligible[nr, nc]:
                continue
            flooded[nr, nc] = True
            queue.append((nr, nc))
    return flooded, int(flooded.sum())


def calculate_flood(
    dem: np.ndarray,
    water_level: float,
    *,
    cell_size_m: float = 30.0,
    routing: bool = False,
    barrier_mask: np.ndarray | None = None,
    source_mask: np.ndarray | None = None,
) -> FloodResult:
    dem = np.asarray(dem, dtype=float)
    barrier = np.zeros_like(dem, dtype=bool) if barrier_mask is None else np.asarray(barrier_mask, dtype=bool)
    eligible = (dem < water_level) & (~barrier)

    if routing:
        sources = default_source_mask(dem.shape) if source_mask is None else np.asarray(source_mask, dtype=bool)
        flooded_mask, connected_cells = _apply_connectivity(eligible, sources)
    else:
        flooded_mask = eligible
        connected_cells = int(flooded_mask.sum())

    depth = np.where(flooded_mask, water_level - dem, 0.0)
    cell_area = float(cell_size_m ** 2)
    flooded_cells = int(flooded_mask.sum())
    flooded_area = flooded_cells * cell_area
    flood_volume = float(depth.sum() * cell_area)
    flooded_percentage = (flooded_cells / dem.size) * 100.0
    max_depth = float(depth.max()) if flooded_cells else 0.0

    return FloodResult(
        water_level_m=float(water_level),
        flooded_mask=flooded_mask,
        depth_m=depth,
        flooded_percentage=float(flooded_percentage),
        flooded_area_m2=float(flooded_area),
        flood_volume_m3=flood_volume,
        max_depth_m=max_depth,
        connected_cells=connected_cells,
        routing_enabled=routing,
    )


def simulate_rising_water(
    dem: np.ndarray,
    water_levels: list[float] | tuple[float, ...] | np.ndarray,
    *,
    cell_size_m: float = 30.0,
    routing: bool = False,
    barrier_mask: np.ndarray | None = None,
    source_mask: np.ndarray | None = None,
) -> list[FloodResult]:
    return [
        calculate_flood(
            dem,
            float(level),
            cell_size_m=cell_size_m,
            routing=routing,
            barrier_mask=barrier_mask,
            source_mask=source_mask,
        )
        for level in water_levels
    ]


def validate_results(dem: np.ndarray, results: list[FloodResult], *, water_levels: list[float] | tuple[float, ...] | np.ndarray) -> dict[str, float | bool]:
    percentages = np.asarray([result.flooded_percentage for result in results], dtype=float)
    max_depths = np.asarray([result.max_depth_m for result in results], dtype=float)
    levels = np.asarray(list(water_levels), dtype=float)
    min_elev = float(np.min(dem))
    max_elev = float(np.max(dem))

    below_min = calculate_flood(dem, min_elev - 1.0)
    above_max = calculate_flood(dem, max_elev + 1.0)
    depth_check = calculate_flood(dem, levels[-1])

    return {
        "monotonic_percentage": bool(np.all(np.diff(percentages) >= -1e-9)),
        "percentage_bounds_ok": bool(np.all((percentages >= 0.0) & (percentages <= 100.0))),
        "edge_below_min_ok": bool(np.isclose(below_min.flooded_percentage, 0.0)),
        "edge_above_max_ok": bool(np.isclose(above_max.flooded_percentage, 100.0)),
        "max_depth_rule_ok": bool(np.isclose(depth_check.max_depth_m, levels[-1] - min_elev, atol=1e-6)),
        "min_elevation_m": min_elev,
        "max_elevation_m": max_elev,
        "final_level_m": float(levels[-1]),
        "final_max_depth_m": float(max_depths[-1]),
    }
