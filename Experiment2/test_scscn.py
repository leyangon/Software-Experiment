from __future__ import annotations

import math
import unittest

import numpy as np

from scscn_runoff import (
    adjust_curve_number,
    calculate_retention,
    calculate_runoff,
    physical_validation,
    route_runoff_time_area,
)


class TestSCSCNRunoff(unittest.TestCase):
    def test_zero_rainfall_returns_zero(self) -> None:
        self.assertEqual(calculate_runoff(0.0, 80.0), 0.0)

    def test_p_less_than_ia_returns_zero(self) -> None:
        retention = calculate_retention(80.0)
        ia = 0.2 * retention
        self.assertEqual(calculate_runoff(ia - 0.01, 80.0), 0.0)

    def test_p_equal_to_ia_returns_zero(self) -> None:
        retention = calculate_retention(80.0)
        ia = 0.2 * retention
        self.assertEqual(calculate_runoff(ia, 80.0), 0.0)

    def test_known_example_matches_guide(self) -> None:
        runoff = calculate_runoff(50.0, 80.0)
        self.assertAlmostEqual(runoff, 13.8, places=1)

    def test_cn_100_returns_rainfall(self) -> None:
        self.assertEqual(calculate_runoff(50.0, 100.0), 50.0)

    def test_cn_0_returns_zero(self) -> None:
        self.assertEqual(calculate_runoff(50.0, 0.0), 0.0)

    def test_runoff_never_exceeds_rainfall(self) -> None:
        rainfall = np.linspace(0.0, 150.0, 50)
        runoff = np.asarray(calculate_runoff(rainfall, 92.0), dtype=float)
        self.assertTrue(np.all(runoff <= rainfall + 1e-9))

    def test_higher_cn_produces_more_runoff(self) -> None:
        rainfall = 50.0
        runoff_values = [float(calculate_runoff(rainfall, cn)) for cn in (60, 70, 80, 90, 95, 100)]
        self.assertEqual(runoff_values, sorted(runoff_values))

    def test_amc_adjustment_direction_is_physical(self) -> None:
        cn_i = adjust_curve_number(80.0, "I")
        cn_ii = adjust_curve_number(80.0, "II")
        cn_iii = adjust_curve_number(80.0, "III")
        self.assertLess(cn_i, cn_ii)
        self.assertLess(cn_ii, cn_iii)

    def test_time_area_routing_preserves_non_negative_series(self) -> None:
        routed = route_runoff_time_area([1.0, 2.0, 3.0], [0.2, 0.5, 0.3])
        self.assertEqual(len(routed), 3)
        self.assertTrue(np.all(routed >= 0.0))
        self.assertTrue(math.isclose(float(routed[0]), 0.2, rel_tol=1e-9))
        self.assertTrue(math.isclose(float(routed[1]), 0.9, rel_tol=1e-9))
        self.assertTrue(math.isclose(float(routed[2]), 1.9, rel_tol=1e-9))

    def test_global_physical_validation(self) -> None:
        validation = physical_validation(range(0, 121, 5), [60, 70, 80, 90, 95, 100])
        self.assertTrue(validation["q_leq_p"])
        self.assertTrue(validation["monotonic_cn"])
        self.assertTrue(validation["zero_rainfall"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
