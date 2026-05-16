from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

import numpy as np
import pandas as pd

AMCLevel = Literal["I", "II", "III"]


@dataclass(frozen=True)
class RunoffResult:
    rainfall_mm: float
    curve_number: float
    adjusted_curve_number: float
    retention_mm: float
    initial_abstraction_mm: float
    runoff_mm: float
    amc: AMCLevel


def _as_float_array(values: float | Iterable[float]) -> np.ndarray:
    if np.isscalar(values):
        return np.asarray([float(values)], dtype=float)
    return np.asarray(list(values), dtype=float)


def _return_scalar_if_needed(original: float | Iterable[float], values: np.ndarray) -> float | np.ndarray:
    if np.isscalar(original):
        return float(values[0])
    return values


def adjust_curve_number(curve_number: float, amc: AMCLevel = "II") -> float:
    """Adjust a standard AMC-II curve number to the selected AMC condition."""
    if curve_number <= 0:
        return 0.0
    if curve_number >= 100:
        return 100.0
    amc = amc.upper()  # type: ignore[assignment]
    if amc == "II":
        return float(curve_number)
    if amc == "I":
        return float(curve_number / (2.281 - 0.01281 * curve_number))
    if amc == "III":
        return float(curve_number / (0.427 + 0.00573 * curve_number))
    raise ValueError("AMC must be 'I', 'II', or 'III'.")


def calculate_retention(curve_number: float) -> float:
    """Return potential maximum retention S in millimetres."""
    if curve_number <= 0:
        return float("inf")
    if curve_number >= 100:
        return 0.0
    return float((25400.0 / curve_number) - 254.0)


def calculate_initial_abstraction(retention_mm: float, ratio: float = 0.2) -> float:
    """Return the initial abstraction Ia in millimetres."""
    if not np.isfinite(retention_mm):
        return float("inf")
    return float(max(0.0, ratio * retention_mm))


def calculate_runoff(
    rainfall_mm: float | Iterable[float],
    curve_number: float,
    amc: AMCLevel = "II",
    ia_ratio: float = 0.2,
) -> float | np.ndarray:
    """Calculate direct runoff depth using the SCS-CN method."""
    rainfall = _as_float_array(rainfall_mm)
    rainfall = np.maximum(rainfall, 0.0)

    adjusted_cn = adjust_curve_number(curve_number, amc)
    if adjusted_cn <= 0:
        runoff = np.zeros_like(rainfall)
        return _return_scalar_if_needed(rainfall_mm, runoff)
    if adjusted_cn >= 100:
        runoff = rainfall.copy()
        return _return_scalar_if_needed(rainfall_mm, runoff)

    retention = calculate_retention(adjusted_cn)
    initial_abstraction = calculate_initial_abstraction(retention, ia_ratio)
    abstraction_excess = rainfall - initial_abstraction

    runoff = np.where(
        abstraction_excess <= 0.0,
        0.0,
        (abstraction_excess**2) / (abstraction_excess + retention),
    )
    runoff = np.clip(runoff, 0.0, rainfall)
    return _return_scalar_if_needed(rainfall_mm, runoff)


def summarize_runoff(rainfall_mm: float, curve_number: float, amc: AMCLevel = "II") -> RunoffResult:
    """Return the intermediate terms and runoff depth for a single case."""
    adjusted_cn = adjust_curve_number(curve_number, amc)
    retention = calculate_retention(adjusted_cn)
    initial_abstraction = calculate_initial_abstraction(retention)
    runoff = float(calculate_runoff(rainfall_mm, curve_number, amc))
    return RunoffResult(
        rainfall_mm=float(max(rainfall_mm, 0.0)),
        curve_number=float(curve_number),
        adjusted_curve_number=float(adjusted_cn),
        retention_mm=float(retention),
        initial_abstraction_mm=float(initial_abstraction),
        runoff_mm=runoff,
        amc=amc,
    )


def build_sensitivity_table(
    rainfall_mm: float,
    curve_numbers: Iterable[float],
    amc: AMCLevel = "II",
) -> pd.DataFrame:
    """Build a CN-vs-runoff table for sensitivity analysis."""
    rows = []
    for cn in curve_numbers:
        result = summarize_runoff(rainfall_mm, float(cn), amc=amc)
        rows.append(
            {
                "rainfall_mm": result.rainfall_mm,
                "curve_number": result.curve_number,
                "adjusted_curve_number": result.adjusted_curve_number,
                "retention_mm": result.retention_mm,
                "initial_abstraction_mm": result.initial_abstraction_mm,
                "runoff_mm": result.runoff_mm,
                "amc": result.amc,
            }
        )
    return pd.DataFrame(rows)


def build_runoff_profiles(
    rainfall_values_mm: Iterable[float],
    curve_numbers: Iterable[float],
    amc: AMCLevel = "II",
) -> pd.DataFrame:
    """Build rainfall-runoff profiles for multiple CN values."""
    rows = []
    rainfall_values = [float(value) for value in rainfall_values_mm]
    for cn in curve_numbers:
        runoff_values = calculate_runoff(rainfall_values, float(cn), amc=amc)
        for rainfall, runoff in zip(rainfall_values, np.asarray(runoff_values, dtype=float)):
            rows.append(
                {
                    "rainfall_mm": rainfall,
                    "curve_number": float(cn),
                    "runoff_mm": float(runoff),
                    "amc": amc,
                }
            )
    return pd.DataFrame(rows)


def route_runoff_time_area(
    excess_rainfall_mm: Iterable[float],
    time_area_weights: Iterable[float],
) -> np.ndarray:
    """Route excess rainfall using a simple time-area weighting curve."""
    rainfall = np.asarray(list(excess_rainfall_mm), dtype=float)
    weights = np.asarray(list(time_area_weights), dtype=float)
    rainfall = np.maximum(rainfall, 0.0)
    weights = np.maximum(weights, 0.0)
    if rainfall.size == 0:
        return np.asarray([], dtype=float)
    if weights.size == 0 or np.allclose(weights.sum(), 0.0):
        raise ValueError("Time-area weights must contain a positive total.")
    normalized_weights = weights / weights.sum()
    return np.convolve(rainfall, normalized_weights, mode="full")[: rainfall.size]


def rational_method_peak_discharge(
    runoff_coefficient: float,
    rainfall_intensity_mm_per_hr: float,
    catchment_area_ha: float,
) -> float:
    """Return peak discharge in m^3/s using the Rational method."""
    coefficient = min(max(runoff_coefficient, 0.0), 1.0)
    intensity = max(rainfall_intensity_mm_per_hr, 0.0)
    area = max(catchment_area_ha, 0.0)
    return 0.00278 * coefficient * intensity * area


def physical_validation(
    rainfall_values_mm: Iterable[float],
    curve_numbers: Iterable[float],
    amc: AMCLevel = "II",
) -> dict[str, bool]:
    """Check key physical expectations of the SCS-CN method."""
    rainfall = np.asarray(list(rainfall_values_mm), dtype=float)
    q_leq_p = True
    monotonic_cn = True
    zero_rainfall = True

    previous_runoff: np.ndarray | None = None
    for cn in curve_numbers:
        runoff = np.asarray(calculate_runoff(rainfall, cn, amc=amc), dtype=float)
        q_leq_p = q_leq_p and bool(np.all(runoff <= rainfall + 1e-9))
        zero_rainfall = zero_rainfall and bool(np.isclose(calculate_runoff(0.0, cn, amc=amc), 0.0))
        if previous_runoff is not None and np.any(runoff < previous_runoff - 1e-9):
            monotonic_cn = False
        previous_runoff = runoff

    return {
        "q_leq_p": q_leq_p,
        "monotonic_cn": monotonic_cn,
        "zero_rainfall": zero_rainfall,
    }


if __name__ == "__main__":
    example = summarize_runoff(50.0, 80.0)
    print(example)
