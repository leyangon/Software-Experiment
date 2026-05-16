from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.optimize import minimize

from .config import ReservoirParameters, SECONDS_PER_DAY


@dataclass
class OptimizationResult:
    releases_m3s: np.ndarray
    storage_m3: np.ndarray
    revenue_usd: float
    ecological_deficit_m3: float
    success: bool
    message: str
    method: str
    objective_value: float
    hard_ecology: bool
    water_quality_enabled: bool


def simulate_storage(
    releases_m3s: Iterable[float],
    inflows_m3s: Iterable[float],
    initial_storage_m3: float,
) -> np.ndarray:
    releases = np.asarray(list(releases_m3s), dtype=float)
    inflows = np.asarray(list(inflows_m3s), dtype=float)
    if releases.shape != inflows.shape:
        raise ValueError("Releases and inflows must have the same length.")
    delta_storage = (inflows - releases) * SECONDS_PER_DAY
    return np.concatenate(([initial_storage_m3], initial_storage_m3 + np.cumsum(delta_storage)))


def calculate_revenue_usd(
    releases_m3s: Iterable[float],
    prices_usd_per_kwh: Iterable[float],
    parameters: ReservoirParameters,
) -> float:
    releases = np.asarray(list(releases_m3s), dtype=float)
    prices = np.asarray(list(prices_usd_per_kwh), dtype=float)
    energy_kwh = releases * SECONDS_PER_DAY * parameters.hydropower_factor_kwh_per_m3
    return float(np.sum(energy_kwh * prices))


def calculate_ecological_deficit_m3(
    releases_m3s: Iterable[float],
    min_release_m3s: float,
) -> float:
    releases = np.asarray(list(releases_m3s), dtype=float)
    deficits_m3s = np.maximum(min_release_m3s - releases, 0.0)
    return float(np.sum(deficits_m3s) * SECONDS_PER_DAY)


def _storage_penalty(storage_m3: np.ndarray, parameters: ReservoirParameters) -> float:
    below = np.maximum(parameters.min_storage_m3 - storage_m3[1:], 0.0)
    above = np.maximum(storage_m3[1:] - parameters.max_storage_m3, 0.0)
    return float(np.sum(below**2 + above**2) / max(parameters.max_storage_m3**2, 1.0))


def _water_quality_penalty(releases_m3s: np.ndarray, storage_m3: np.ndarray, parameters: ReservoirParameters) -> float:
    low_storage = np.maximum(parameters.water_quality_min_storage_m3 - storage_m3[1:], 0.0)
    release_steps = np.diff(releases_m3s, prepend=releases_m3s[0])
    rapid_changes = np.maximum(np.abs(release_steps) - parameters.max_release_step_m3s, 0.0)
    return float(
        np.sum(low_storage**2) / max(parameters.water_quality_min_storage_m3**2, 1.0)
        + np.sum(rapid_changes**2) / max(parameters.max_release_step_m3s**2, 1.0)
    )


def _build_constraints(
    parameters: ReservoirParameters,
    inflows_m3s: np.ndarray,
    hard_ecology: bool,
    water_quality: bool,
) -> list[dict[str, object]]:
    constraints: list[dict[str, object]] = []
    for day in range(parameters.num_days):
        constraints.append(
            {
                "type": "ineq",
                "fun": lambda x, idx=day: simulate_storage(x, inflows_m3s, parameters.current_storage_m3)[idx + 1]
                - parameters.min_storage_m3,
            }
        )
        constraints.append(
            {
                "type": "ineq",
                "fun": lambda x, idx=day: parameters.max_storage_m3
                - simulate_storage(x, inflows_m3s, parameters.current_storage_m3)[idx + 1],
            }
        )
        if hard_ecology:
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda x, idx=day: x[idx] - parameters.min_ecological_release_m3s,
                }
            )
        if water_quality:
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda x, idx=day: simulate_storage(x, inflows_m3s, parameters.current_storage_m3)[idx + 1]
                    - parameters.water_quality_min_storage_m3,
                }
            )
            if day > 0:
                constraints.append(
                    {
                        "type": "ineq",
                        "fun": lambda x, idx=day: parameters.max_release_step_m3s - abs(x[idx] - x[idx - 1]),
                    }
                )
    return constraints


def optimize_releases(
    parameters: ReservoirParameters,
    inflows_m3s: Iterable[float] | None = None,
    ecology_weight: float = 1.0,
    hard_ecology: bool = True,
    method: str = "SLSQP",
    water_quality: bool = False,
) -> OptimizationResult:
    source_inflows = parameters.inflow_forecast_m3s if inflows_m3s is None else inflows_m3s
    inflows = np.asarray(list(source_inflows), dtype=float)
    lower_bound = parameters.min_ecological_release_m3s if hard_ecology else 0.0
    bounds = [(lower_bound, parameters.max_release_m3s) for _ in range(parameters.num_days)]
    initial_guess = np.clip(inflows, lower_bound, parameters.max_release_m3s)
    if water_quality:
        initial_guess = np.maximum(initial_guess, lower_bound)
        initial_guess = np.minimum.accumulate(initial_guess[::-1])[::-1]
        initial_guess = np.clip(initial_guess, lower_bound, parameters.max_release_m3s)

    max_revenue = calculate_revenue_usd(
        [parameters.max_release_m3s] * parameters.num_days,
        parameters.hydropower_price_usd_per_kwh,
        parameters,
    )
    max_deficit = parameters.min_ecological_release_m3s * parameters.num_days * SECONDS_PER_DAY

    def objective(x: np.ndarray) -> float:
        storage = simulate_storage(x, inflows, parameters.current_storage_m3)
        revenue = calculate_revenue_usd(x, parameters.hydropower_price_usd_per_kwh, parameters)
        deficit = calculate_ecological_deficit_m3(x, parameters.min_ecological_release_m3s)
        revenue_term = revenue / max(max_revenue, 1.0)
        deficit_term = deficit / max(max_deficit, 1.0)
        value = -((1.0 - ecology_weight) * revenue_term - ecology_weight * deficit_term)
        if method.upper() == "L-BFGS-B":
            penalty = 250.0 * _storage_penalty(storage, parameters)
            if hard_ecology:
                hard_deficit = calculate_ecological_deficit_m3(x, parameters.min_ecological_release_m3s)
                penalty += 100.0 * (hard_deficit / max(max_deficit, 1.0))
            if water_quality:
                penalty += 50.0 * _water_quality_penalty(x, storage, parameters)
            value += penalty
        return float(value)

    constraints = [] if method.upper() == "L-BFGS-B" else _build_constraints(parameters, inflows, hard_ecology, water_quality)
    result = minimize(
        objective,
        initial_guess,
        method=method,
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1_000, "ftol": 1e-9},
    )

    releases = np.clip(result.x, lower_bound, parameters.max_release_m3s)
    storage = simulate_storage(releases, inflows, parameters.current_storage_m3)
    return OptimizationResult(
        releases_m3s=releases,
        storage_m3=storage,
        revenue_usd=calculate_revenue_usd(releases, parameters.hydropower_price_usd_per_kwh, parameters),
        ecological_deficit_m3=calculate_ecological_deficit_m3(releases, parameters.min_ecological_release_m3s),
        success=bool(result.success),
        message=str(result.message),
        method=method,
        objective_value=float(result.fun),
        hard_ecology=hard_ecology,
        water_quality_enabled=water_quality,
    )


def generate_pareto_frontier(parameters: ReservoirParameters) -> list[dict[str, float]]:
    frontier: list[dict[str, float]] = []
    for ecology_weight in parameters.pareto_weights:
        result = optimize_releases(
            parameters,
            ecology_weight=ecology_weight,
            hard_ecology=False,
            method="SLSQP",
            water_quality=False,
        )
        frontier.append(
            {
                "ecology_weight": ecology_weight,
                "revenue_usd": result.revenue_usd,
                "ecological_deficit_m3": result.ecological_deficit_m3,
                "min_release_m3s": float(np.min(result.releases_m3s)),
                "max_release_m3s": float(np.max(result.releases_m3s)),
            }
        )
    return frontier


def evaluate_constraints(result: OptimizationResult, parameters: ReservoirParameters) -> dict[str, bool | float]:
    releases_ok = bool(np.all(result.releases_m3s <= parameters.max_release_m3s + 1e-6))
    minimum_release_ok = bool(np.all(result.releases_m3s >= parameters.min_ecological_release_m3s - 1e-6))
    storage_ok = bool(
        np.all(result.storage_m3[1:] >= parameters.min_storage_m3 - 1e-6)
        and np.all(result.storage_m3[1:] <= parameters.max_storage_m3 + 1e-6)
    )
    mass_balance_residual = []
    inflows = np.asarray(parameters.inflow_forecast_m3s, dtype=float)
    for day in range(parameters.num_days):
        lhs = result.storage_m3[day + 1]
        rhs = result.storage_m3[day] + (inflows[day] - result.releases_m3s[day]) * SECONDS_PER_DAY
        mass_balance_residual.append(abs(lhs - rhs))
    return {
        "release_bounds_ok": releases_ok,
        "minimum_release_ok": minimum_release_ok,
        "storage_bounds_ok": storage_ok,
        "mass_balance_ok": bool(max(mass_balance_residual) <= 1e-4),
        "max_mass_balance_residual_m3": float(max(mass_balance_residual)),
        "total_revenue_usd": float(result.revenue_usd),
    }


def compare_algorithms(parameters: ReservoirParameters) -> list[dict[str, float | str | bool]]:
    records: list[dict[str, float | str | bool]] = []
    for method in ("SLSQP", "L-BFGS-B"):
        result = optimize_releases(parameters, ecology_weight=0.15, hard_ecology=True, method=method)
        validation = evaluate_constraints(result, parameters)
        records.append(
            {
                "method": method,
                "success": result.success,
                "revenue_usd": result.revenue_usd,
                "ecological_deficit_m3": result.ecological_deficit_m3,
                "objective_value": result.objective_value,
                "storage_bounds_ok": bool(validation["storage_bounds_ok"]),
                "minimum_release_ok": bool(validation["minimum_release_ok"]),
            }
        )
    return records


def rolling_horizon_dispatch(parameters: ReservoirParameters) -> dict[str, np.ndarray | float]:
    planned_releases: list[float] = []
    storage = parameters.current_storage_m3
    actual_inflows = np.asarray(parameters.rolling_horizon_actual_inflow_m3s, dtype=float)
    prices = np.asarray(parameters.hydropower_price_usd_per_kwh, dtype=float)
    storage_trace = [storage]

    for day in range(parameters.num_days):
        remaining_inflows = tuple(actual_inflows[day:])
        remaining_prices = tuple(prices[day:])
        sub_parameters = ReservoirParameters(
            current_storage_m3=storage,
            min_storage_m3=parameters.min_storage_m3,
            max_storage_m3=parameters.max_storage_m3,
            min_ecological_release_m3s=parameters.min_ecological_release_m3s,
            max_release_m3s=parameters.max_release_m3s,
            inflow_forecast_m3s=remaining_inflows,
            hydropower_price_usd_per_kwh=remaining_prices,
            hydropower_head_m=parameters.hydropower_head_m,
            turbine_efficiency=parameters.turbine_efficiency,
            water_quality_min_storage_m3=parameters.water_quality_min_storage_m3,
            max_release_step_m3s=parameters.max_release_step_m3s,
            robust_risk_aversion=parameters.robust_risk_aversion,
            pareto_weights=parameters.pareto_weights,
            scenario_names=parameters.scenario_names,
            scenario_matrix_m3s=parameters.scenario_matrix_m3s,
            rolling_horizon_actual_inflow_m3s=tuple(actual_inflows[day:]),
            report_date=parameters.report_date,
            student_name=parameters.student_name,
            class_name=parameters.class_name,
            student_id=parameters.student_id,
            email=parameters.email,
        )
        sub_result = optimize_releases(sub_parameters, ecology_weight=0.15, hard_ecology=True, method="SLSQP")
        today_release = float(sub_result.releases_m3s[0])
        planned_releases.append(today_release)
        storage = storage + (actual_inflows[day] - today_release) * SECONDS_PER_DAY
        storage_trace.append(storage)

    releases_array = np.asarray(planned_releases, dtype=float)
    return {
        "releases_m3s": releases_array,
        "storage_m3": np.asarray(storage_trace, dtype=float),
        "revenue_usd": calculate_revenue_usd(releases_array, prices, parameters),
    }


def robust_uncertainty_analysis(parameters: ReservoirParameters) -> list[dict[str, float | str]]:
    scenario_records: list[dict[str, float | str]] = []
    scenarios = [np.asarray(values, dtype=float) for values in parameters.scenario_matrix_m3s]

    bounds = [
        (parameters.min_ecological_release_m3s, parameters.max_release_m3s)
        for _ in range(parameters.num_days)
    ]
    initial_guess = np.clip(
        np.mean(np.vstack(scenarios), axis=0),
        parameters.min_ecological_release_m3s,
        parameters.max_release_m3s,
    )
    max_revenue = calculate_revenue_usd(
        [parameters.max_release_m3s] * parameters.num_days,
        parameters.hydropower_price_usd_per_kwh,
        parameters,
    )

    def robust_objective(x: np.ndarray) -> float:
        revenue = calculate_revenue_usd(x, parameters.hydropower_price_usd_per_kwh, parameters)
        return float(-(revenue / max(max_revenue, 1.0)))

    constraints: list[dict[str, object]] = []
    for inflows in scenarios:
        for day in range(parameters.num_days):
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda x, seq=inflows, idx=day: simulate_storage(
                        x,
                        seq,
                        parameters.current_storage_m3,
                    )[idx + 1]
                    - parameters.min_storage_m3,
                }
            )
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda x, seq=inflows, idx=day: parameters.max_storage_m3
                    - simulate_storage(x, seq, parameters.current_storage_m3)[idx + 1],
                }
            )

    robust = minimize(
        robust_objective,
        initial_guess,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1_000, "ftol": 1e-9},
    )
    robust_releases = np.clip(robust.x, parameters.min_ecological_release_m3s, parameters.max_release_m3s)

    for name, inflows in zip(parameters.scenario_names, scenarios):
        scenario_revenue = calculate_revenue_usd(robust_releases, parameters.hydropower_price_usd_per_kwh, parameters)
        storage = simulate_storage(robust_releases, inflows, parameters.current_storage_m3)
        feasible = bool(
            np.all(storage[1:] >= parameters.min_storage_m3 - 1e-6)
            and np.all(storage[1:] <= parameters.max_storage_m3 + 1e-6)
        )
        scenario_records.append(
            {
                "scenario": name,
                "mean_inflow_m3s": float(np.mean(inflows)),
                "revenue_usd": scenario_revenue,
                "final_storage_m3": float(storage[-1]),
                "feasible_storage": feasible,
            }
        )
    return scenario_records


def water_quality_extension(parameters: ReservoirParameters) -> OptimizationResult:
    return optimize_releases(
        parameters,
        ecology_weight=0.25,
        hard_ecology=True,
        method="SLSQP",
        water_quality=True,
    )
