from __future__ import annotations

from dataclasses import dataclass, field


SECONDS_PER_DAY = 86_400.0
WATER_DENSITY = 1_000.0
GRAVITY = 9.81
JOULES_PER_KWH = 3.6e6


@dataclass(frozen=True)
class ReservoirParameters:
    current_storage_m3: float = 500_000.0
    min_storage_m3: float = 100_000.0
    max_storage_m3: float = 1_000_000.0
    min_ecological_release_m3s: float = 10.0
    max_release_m3s: float = 100.0
    inflow_forecast_m3s: tuple[float, ...] = (15.0, 12.0, 10.0, 8.0, 12.0, 15.0, 18.0)
    hydropower_price_usd_per_kwh: tuple[float, ...] = (0.08, 0.08, 0.08, 0.08, 0.10, 0.12, 0.10)
    hydropower_head_m: float = 25.0
    turbine_efficiency: float = 0.90
    water_quality_min_storage_m3: float = 250_000.0
    max_release_step_m3s: float = 25.0
    robust_risk_aversion: float = 0.25
    pareto_weights: tuple[float, ...] = tuple(round(weight, 2) for weight in (0.0, 0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 0.9, 1.0))
    scenario_names: tuple[str, ...] = ("baseline", "dry", "wetter_start", "late_recovery", "volatile")
    scenario_matrix_m3s: tuple[tuple[float, ...], ...] = (
        (15.0, 12.0, 10.0, 8.0, 12.0, 15.0, 18.0),
        (12.0, 10.0, 8.0, 6.0, 10.0, 12.0, 14.0),
        (18.0, 15.0, 12.0, 10.0, 11.0, 13.0, 15.0),
        (10.0, 9.0, 8.0, 7.0, 12.0, 18.0, 22.0),
        (20.0, 8.0, 16.0, 5.0, 14.0, 10.0, 24.0),
    )
    rolling_horizon_actual_inflow_m3s: tuple[float, ...] = (14.0, 11.0, 9.0, 7.0, 11.0, 17.0, 20.0)
    report_date: str = "2026-04-21"
    student_name: str = "刘子康"
    class_name: str = "S4280"
    student_id: str = "3124358273"
    email: str = "leyangon@qq.com"

    @property
    def num_days(self) -> int:
        return len(self.inflow_forecast_m3s)

    @property
    def hydropower_factor_kwh_per_m3(self) -> float:
        return (
            self.turbine_efficiency
            * WATER_DENSITY
            * GRAVITY
            * self.hydropower_head_m
            / JOULES_PER_KWH
        )


@dataclass(frozen=True)
class ProjectPaths:
    root_name: str = "Experiment3"
    result_dir_name: str = "results"
    data_dir_name: str = "data"
    test_dir_name: str = "tests"
    source_dir_name: str = "src"
    deliverables: tuple[str, ...] = field(
        default_factory=lambda: (
            "reservoir_optimize.py",
            "optimal_schedule.csv",
            "tradeoff_analysis.png",
            "prompt_log.md",
            "validation_report.txt",
        )
    )
