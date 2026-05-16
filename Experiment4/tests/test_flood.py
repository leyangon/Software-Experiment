from __future__ import annotations

import unittest

import numpy as np

from src.dem_io import building_barrier_mask, generate_synthetic_dem
from src.config import FloodConfig
from src.flood import calculate_flood, simulate_rising_water, validate_results


class FloodInundationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = FloodConfig()
        self.dem = generate_synthetic_dem(self.config)

    def test_edge_case_below_min_has_zero_flooding(self) -> None:
        result = calculate_flood(self.dem, float(self.dem.min()) - 0.5)
        self.assertAlmostEqual(result.flooded_percentage, 0.0)
        self.assertAlmostEqual(result.max_depth_m, 0.0)

    def test_edge_case_above_max_floods_all_cells(self) -> None:
        result = calculate_flood(self.dem, float(self.dem.max()) + 0.5)
        self.assertAlmostEqual(result.flooded_percentage, 100.0)

    def test_monotonic_growth_for_rising_levels(self) -> None:
        levels = [40.0, 42.0, 44.0, 46.0, 48.0, 50.0]
        results = simulate_rising_water(self.dem, levels)
        validation = validate_results(self.dem, results, water_levels=levels)
        self.assertTrue(validation["monotonic_percentage"])
        self.assertTrue(validation["percentage_bounds_ok"])

    def test_routing_never_exceeds_direct_flood_extent(self) -> None:
        direct = calculate_flood(self.dem, 50.0, routing=False)
        routed = calculate_flood(self.dem, 50.0, routing=True)
        self.assertLessEqual(routed.flooded_percentage, direct.flooded_percentage)

    def test_building_barriers_reduce_routed_flooding(self) -> None:
        mask = building_barrier_mask(self.dem.shape)
        routed = calculate_flood(self.dem, 50.0, routing=True)
        barrier = calculate_flood(self.dem, 50.0, routing=True, barrier_mask=mask)
        self.assertLessEqual(barrier.flooded_percentage, routed.flooded_percentage)


if __name__ == "__main__":
    unittest.main()
