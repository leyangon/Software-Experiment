from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import DATA_DIR, FloodConfig


def _scale_to_range(values: np.ndarray, low: float, high: float) -> np.ndarray:
    minimum = float(values.min())
    maximum = float(values.max())
    if np.isclose(maximum, minimum):
        return np.full_like(values, low, dtype=float)
    scaled = (values - minimum) / (maximum - minimum)
    return low + scaled * (high - low)


def generate_synthetic_dem(config: FloodConfig) -> np.ndarray:
    rows, cols = config.grid_shape
    rng = np.random.default_rng(config.random_seed)

    y = np.linspace(0.0, 1.0, rows)
    x = np.linspace(0.0, 1.0, cols)
    xx, yy = np.meshgrid(x, y)

    slope = 0.9 * xx + 0.4 * yy
    basin = -1.8 * np.exp(-(((xx - 0.35) ** 2) / 0.03 + ((yy - 0.55) ** 2) / 0.06))
    floodplain = -1.2 * np.exp(-(((xx - 0.62) ** 2) / 0.04 + ((yy - 0.42) ** 2) / 0.03))
    ridge = 0.8 * np.exp(-(((xx - 0.78) ** 2) / 0.02 + ((yy - 0.72) ** 2) / 0.04))
    channel = -0.9 * np.exp(-((yy - (0.28 + 0.18 * np.sin(2.5 * np.pi * xx))) ** 2) / 0.003)
    undulation = 0.2 * np.sin(4 * np.pi * xx) + 0.15 * np.cos(3 * np.pi * yy)
    noise = rng.normal(0.0, 0.05, size=(rows, cols))

    raw = slope + basin + floodplain + ridge + channel + undulation + noise
    dem = _scale_to_range(
        raw,
        config.synthetic_min_elevation_m,
        config.synthetic_max_elevation_m,
    )
    return np.round(dem, 3)


def building_barrier_mask(shape: tuple[int, int]) -> np.ndarray:
    rows, cols = shape
    mask = np.zeros((rows, cols), dtype=bool)
    footprints = [
        (18, 26, 10, 22),
        (28, 38, 15, 30),
        (42, 56, 24, 38),
        (56, 70, 45, 58),
        (36, 48, 58, 74),
        (18, 30, 70, 84),
        (62, 80, 74, 90),
    ]
    for r0, r1, c0, c1 in footprints:
        mask[r0:r1, c0:c1] = True
    return mask


def _nearest_resize(dem: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    row_idx = np.linspace(0, dem.shape[0] - 1, shape[0]).astype(int)
    col_idx = np.linspace(0, dem.shape[1] - 1, shape[1]).astype(int)
    return dem[np.ix_(row_idx, col_idx)]


def load_real_dem_sample(config: FloodConfig) -> tuple[np.ndarray, str]:
    try:
        from matplotlib import cbook
    except Exception as exc:  # pragma: no cover - dependency failure only
        raise RuntimeError("matplotlib is required to load the real DEM sample") from exc

    dataset_path = cbook.get_sample_data(config.real_dem_dataset_name, asfileobj=False)
    contents = np.load(dataset_path)
    elevation = np.asarray(contents["elevation"], dtype=float)
    resized = _nearest_resize(elevation, config.grid_shape)
    normalized = _scale_to_range(
        resized,
        config.synthetic_min_elevation_m,
        config.synthetic_max_elevation_m,
    )
    return np.round(normalized, 3), str(dataset_path)


def save_dem(dem: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, dem)


def load_dem(filepath: Path | None = None, *, use_real_sample: bool = False, config: FloodConfig | None = None) -> tuple[np.ndarray, dict[str, str]]:
    cfg = config or FloodConfig()
    if filepath is not None:
        dem = np.load(filepath)
        return np.asarray(dem, dtype=float), {"source": str(filepath), "type": "file"}
    if use_real_sample:
        dem, source_path = load_real_dem_sample(cfg)
        return dem, {"source": source_path, "type": "real_sample"}
    dem = generate_synthetic_dem(cfg)
    return dem, {"source": "synthetic_generator", "type": "synthetic"}
