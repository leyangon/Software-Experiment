from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class StudentMetadata:
    name: str = "刘子康"
    class_name: str = "S4280"
    student_id: str = "3124358273"
    email: str = "leyangon@qq.com"
    report_date: str = str(date(2026, 4, 21))


@dataclass(frozen=True)
class FloodConfig:
    grid_shape: tuple[int, int] = (100, 100)
    cell_size_m: float = 30.0
    base_water_levels: tuple[float, ...] = tuple(np.arange(40.0, 51.0, 1.0))
    required_levels: tuple[float, float] = (40.0, 50.0)
    synthetic_min_elevation_m: float = 30.0
    synthetic_max_elevation_m: float = 80.0
    random_seed: int = 42
    project_name: str = "Experiment4"
    real_dem_dataset_name: str = "jacksboro_fault_dem.npz"
    real_dem_label: str = "Jacksboro fault DEM sample"


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
