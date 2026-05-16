from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis import export_extension_tables, save_summary_json, save_tradeoff_plot, schedule_to_dataframe
from src.config import ReservoirParameters
from src.optimization import (
    compare_algorithms,
    evaluate_constraints,
    generate_pareto_frontier,
    optimize_releases,
    robust_uncertainty_analysis,
    rolling_horizon_dispatch,
    water_quality_extension,
)


PROJECT_ROOT = Path(__file__).resolve().parent


def build_validation_report(validation: dict[str, bool | float], result_message: str) -> str:
    lines = [
        "Reservoir Optimization Validation Report",
        "=" * 40,
        f"Optimizer message: {result_message}",
        f"Release bounds satisfied: {validation['release_bounds_ok']}",
        f"Minimum ecological release satisfied: {validation['minimum_release_ok']}",
        f"Storage bounds satisfied: {validation['storage_bounds_ok']}",
        f"Mass balance satisfied: {validation['mass_balance_ok']}",
        f"Maximum mass balance residual (m^3): {validation['max_mass_balance_residual_m3']:.6f}",
        f"Total revenue (USD): {validation['total_revenue_usd']:.2f}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parameters = ReservoirParameters()
    (PROJECT_ROOT / "results").mkdir(parents=True, exist_ok=True)

    baseline = optimize_releases(parameters, ecology_weight=0.15, hard_ecology=True, method="SLSQP")
    schedule_df = schedule_to_dataframe(
        releases_m3s=baseline.releases_m3s,
        storage_m3=baseline.storage_m3,
        inflows_m3s=parameters.inflow_forecast_m3s,
        prices_usd_per_kwh=parameters.hydropower_price_usd_per_kwh,
        power_factor_kwh_per_m3=parameters.hydropower_factor_kwh_per_m3,
    )
    schedule_df.to_csv(PROJECT_ROOT / "optimal_schedule.csv", index=False)

    frontier_records = generate_pareto_frontier(parameters)
    frontier_df = pd.DataFrame(frontier_records)
    save_tradeoff_plot(frontier_df, PROJECT_ROOT / "tradeoff_analysis.png")

    validation = evaluate_constraints(baseline, parameters)
    validation_text = build_validation_report(validation, baseline.message)
    (PROJECT_ROOT / "validation_report.txt").write_text(validation_text, encoding="utf-8")

    uncertainty_records = robust_uncertainty_analysis(parameters)
    algorithm_records = compare_algorithms(parameters)
    rolling_horizon = rolling_horizon_dispatch(parameters)
    water_quality = water_quality_extension(parameters)

    water_quality_df = schedule_to_dataframe(
        releases_m3s=water_quality.releases_m3s,
        storage_m3=water_quality.storage_m3,
        inflows_m3s=parameters.inflow_forecast_m3s,
        prices_usd_per_kwh=parameters.hydropower_price_usd_per_kwh,
        power_factor_kwh_per_m3=parameters.hydropower_factor_kwh_per_m3,
    )
    water_quality_df.to_csv(PROJECT_ROOT / "results" / "water_quality_schedule.csv", index=False)

    export_extension_tables(
        parameters=parameters,
        frontier_records=frontier_records,
        uncertainty_records=uncertainty_records,
        algorithm_records=algorithm_records,
        rolling_horizon=rolling_horizon,
        project_root=PROJECT_ROOT,
    )

    summary = {
        "baseline_revenue_usd": round(baseline.revenue_usd, 2),
        "baseline_min_release_m3s": round(float(schedule_df["release_m3s"].min()), 4),
        "baseline_final_storage_m3": round(float(schedule_df["storage_end_m3"].iloc[-1]), 2),
        "water_quality_revenue_usd": round(water_quality.revenue_usd, 2),
        "rolling_horizon_revenue_usd": round(float(rolling_horizon["revenue_usd"]), 2),
        "pareto_best_revenue_usd": round(float(frontier_df["revenue_usd"].max()), 2),
        "pareto_lowest_deficit_m3": round(float(frontier_df["ecological_deficit_m3"].min()), 2),
        "algorithm_comparison": algorithm_records,
        "uncertainty_summary": uncertainty_records,
    }
    save_summary_json(summary, PROJECT_ROOT / "results" / "summary.json")

    print(f"Optimization complete. Revenue = ${baseline.revenue_usd:,.2f}")
    print(f"Validation report written to {PROJECT_ROOT / 'validation_report.txt'}")


if __name__ == "__main__":
    main()
