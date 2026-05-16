from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.config import DATA_DIR, PROJECT_ROOT, RESULTS_DIR, FloodConfig
from src.dem_io import building_barrier_mask, load_dem, save_dem
from src.flood import calculate_flood, simulate_rising_water, validate_results
from src.visualization import (
    save_animation_gif,
    save_flood_curve,
    save_flood_figure,
    save_multi_level_comparison,
)


def _write_validation_report(validation: dict[str, float | bool], output_path: Path) -> None:
    lines = [
        "Flood Inundation Validation Report",
        "=" * 40,
        f"Flooded area increases monotonically: {validation['monotonic_percentage']}",
        f"Flooded percentage always within 0-100%: {validation['percentage_bounds_ok']}",
        f"Edge case below minimum elevation behaves correctly: {validation['edge_below_min_ok']}",
        f"Edge case above maximum elevation behaves correctly: {validation['edge_above_max_ok']}",
        f"Maximum depth follows water_level - min_elevation: {validation['max_depth_rule_ok']}",
        f"Minimum elevation (m): {validation['min_elevation_m']:.3f}",
        f"Maximum elevation (m): {validation['max_elevation_m']:.3f}",
        f"Final test level (m): {validation['final_level_m']:.3f}",
        f"Final maximum depth (m): {validation['final_max_depth_m']:.3f}",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _results_to_records(results: list) -> list[dict[str, float | int | bool]]:
    return [
        {
            "water_level_m": result.water_level_m,
            "flooded_percentage": result.flooded_percentage,
            "flooded_area_m2": result.flooded_area_m2,
            "flood_volume_m3": result.flood_volume_m3,
            "max_depth_m": result.max_depth_m,
            "connected_cells": result.connected_cells,
            "routing_enabled": result.routing_enabled,
        }
        for result in results
    ]


def main() -> None:
    config = FloodConfig()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    dem, dem_meta = load_dem(config=config)
    save_dem(dem, PROJECT_ROOT / "dem_data.npy")

    building_mask = building_barrier_mask(dem.shape)
    base_levels = list(config.base_water_levels)
    base_results = simulate_rising_water(dem, base_levels, cell_size_m=config.cell_size_m)

    validation = validate_results(dem, base_results, water_levels=base_levels)
    _write_validation_report(validation, PROJECT_ROOT / "validation_report.txt")

    required_lookup = {
        level: calculate_flood(dem, level, cell_size_m=config.cell_size_m)
        for level in config.required_levels
    }
    save_flood_figure(dem, required_lookup[40.0], PROJECT_ROOT / "flood_extent_40m.png")
    save_flood_figure(dem, required_lookup[50.0], PROJECT_ROOT / "flood_extent_50m.png")
    save_flood_curve(base_results, PROJECT_ROOT / "flood_curve.png")

    comparison_levels = [40.0, 43.0, 46.0, 50.0]
    comparison_results = [calculate_flood(dem, level, cell_size_m=config.cell_size_m) for level in comparison_levels]
    save_multi_level_comparison(dem, comparison_results, RESULTS_DIR / "water_level_comparison.png")

    routed_results = simulate_rising_water(
        dem,
        base_levels,
        cell_size_m=config.cell_size_m,
        routing=True,
    )
    routed_50 = calculate_flood(dem, 50.0, cell_size_m=config.cell_size_m, routing=True)
    save_flood_figure(
        dem,
        routed_50,
        RESULTS_DIR / "flood_routing_50m.png",
        suptitle="Flood Routing Result at 50 m",
    )

    barrier_results = simulate_rising_water(
        dem,
        base_levels,
        cell_size_m=config.cell_size_m,
        routing=True,
        barrier_mask=building_mask,
    )
    barrier_50 = calculate_flood(
        dem,
        50.0,
        cell_size_m=config.cell_size_m,
        routing=True,
        barrier_mask=building_mask,
    )
    save_flood_figure(
        dem,
        barrier_50,
        RESULTS_DIR / "flood_with_buildings_50m.png",
        barrier_mask=building_mask,
        suptitle="Flood Routing with Building Barriers at 50 m",
    )

    save_animation_gif(dem, base_results, RESULTS_DIR / "rising_water.gif")

    real_dem, real_dem_meta = load_dem(config=config, use_real_sample=True)
    np.save(DATA_DIR / "real_dem_sample.npy", real_dem)
    real_dem_result = calculate_flood(real_dem, 50.0, cell_size_m=config.cell_size_m)
    save_flood_figure(
        real_dem,
        real_dem_result,
        RESULTS_DIR / "real_dem_flood_50m.png",
        suptitle="Real DEM Sample Flood Analysis at 50 m",
    )

    summary = {
        "dem_source": dem_meta,
        "real_dem_source": real_dem_meta,
        "grid_shape": list(dem.shape),
        "cell_size_m": config.cell_size_m,
        "water_levels_m": base_levels,
        "validation": validation,
        "baseline_results": _results_to_records(base_results),
        "routed_results": _results_to_records(routed_results),
        "barrier_results": _results_to_records(barrier_results),
        "building_cells": int(building_mask.sum()),
        "real_dem_result_50m": {
            "flooded_percentage": real_dem_result.flooded_percentage,
            "flood_volume_m3": real_dem_result.flood_volume_m3,
            "max_depth_m": real_dem_result.max_depth_m,
        },
    }
    (RESULTS_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Flood inundation analysis complete.")
    print(f"DEM saved to {PROJECT_ROOT / 'dem_data.npy'}")
    print(f"Validation report saved to {PROJECT_ROOT / 'validation_report.txt'}")


if __name__ == "__main__":
    main()
