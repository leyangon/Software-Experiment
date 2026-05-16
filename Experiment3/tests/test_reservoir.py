from __future__ import annotations

import unittest

import numpy as np

from src.config import ReservoirParameters
from src.optimization import (
    compare_algorithms,
    evaluate_constraints,
    optimize_releases,
    rolling_horizon_dispatch,
    simulate_storage,
    water_quality_extension,
)


class ReservoirOptimizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = ReservoirParameters()

    def test_storage_simulation_length(self) -> None:
        releases = [10.0] * self.parameters.num_days
        storage = simulate_storage(releases, self.parameters.inflow_forecast_m3s, self.parameters.current_storage_m3)
        self.assertEqual(len(storage), self.parameters.num_days + 1)

    def test_baseline_solution_meets_constraints(self) -> None:
        result = optimize_releases(self.parameters, ecology_weight=0.15, hard_ecology=True)
        validation = evaluate_constraints(result, self.parameters)
        self.assertTrue(result.success)
        self.assertTrue(validation["storage_bounds_ok"])
        self.assertTrue(validation["minimum_release_ok"])
        self.assertTrue(validation["mass_balance_ok"])

    def test_revenue_is_positive(self) -> None:
        result = optimize_releases(self.parameters, ecology_weight=0.15, hard_ecology=True)
        self.assertGreater(result.revenue_usd, 0.0)

    def test_rolling_horizon_respects_storage_limits(self) -> None:
        result = rolling_horizon_dispatch(self.parameters)
        storage = np.asarray(result["storage_m3"], dtype=float)
        self.assertTrue(np.all(storage[1:] >= self.parameters.min_storage_m3 - 1e-6))
        self.assertTrue(np.all(storage[1:] <= self.parameters.max_storage_m3 + 1e-6))

    def test_water_quality_extension_respects_stricter_limits(self) -> None:
        result = water_quality_extension(self.parameters)
        self.assertTrue(np.all(result.storage_m3[1:] >= self.parameters.water_quality_min_storage_m3 - 1e-6))

    def test_algorithm_comparison_contains_two_methods(self) -> None:
        records = compare_algorithms(self.parameters)
        self.assertEqual({record["method"] for record in records}, {"SLSQP", "L-BFGS-B"})


if __name__ == "__main__":
    unittest.main()
