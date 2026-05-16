from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - fallback path only used when matplotlib is missing.
    plt = None
    from PIL import Image, ImageDraw

from .config import ReservoirParameters


def schedule_to_dataframe(
    releases_m3s: Iterable[float],
    storage_m3: Iterable[float],
    inflows_m3s: Iterable[float],
    prices_usd_per_kwh: Iterable[float],
    power_factor_kwh_per_m3: float,
) -> pd.DataFrame:
    releases = list(releases_m3s)
    storage = list(storage_m3)
    inflows = list(inflows_m3s)
    prices = list(prices_usd_per_kwh)
    rows = []
    for day, (release, inflow, price) in enumerate(zip(releases, inflows, prices), start=1):
        volume_m3 = release * 86_400.0
        energy_kwh = volume_m3 * power_factor_kwh_per_m3
        rows.append(
            {
                "day": day,
                "inflow_m3s": round(inflow, 4),
                "release_m3s": round(release, 4),
                "storage_start_m3": round(storage[day - 1], 4),
                "storage_end_m3": round(storage[day], 4),
                "hydropower_price_usd_per_kwh": round(price, 4),
                "energy_generated_kwh": round(energy_kwh, 4),
                "revenue_usd": round(energy_kwh * price, 4),
            }
        )
    return pd.DataFrame(rows)


def save_tradeoff_plot(frontier: pd.DataFrame, output_path: Path) -> None:
    if plt is not None:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(frontier["ecological_deficit_m3"], frontier["revenue_usd"], marker="o", color="#1b6ca8")
        for _, row in frontier.iterrows():
            ax.annotate(f"w={row['ecology_weight']:.2f}", (row["ecological_deficit_m3"], row["revenue_usd"]), fontsize=8)
        ax.set_xlabel("Ecological deficit (m^3)")
        ax.set_ylabel("Hydropower revenue (USD)")
        ax.set_title("Pareto Frontier: Ecology vs Hydropower Revenue")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(output_path, dpi=200)
        plt.close(fig)
        return

    image = Image.new("RGB", (1000, 620), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 20), "Pareto Frontier: Ecology vs Hydropower Revenue", fill="black")
    draw.rectangle((90, 80, 930, 540), outline="black", width=2)
    xs = frontier["ecological_deficit_m3"].tolist()
    ys = frontier["revenue_usd"].tolist()
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    points = []
    for x, y in zip(xs, ys):
        px = 110 + (x - min_x) / max(max_x - min_x, 1.0) * 780
        py = 520 - (y - min_y) / max(max_y - min_y, 1.0) * 420
        points.append((px, py))
    if len(points) > 1:
        draw.line(points, fill="#1b6ca8", width=3)
    for point, weight in zip(points, frontier["ecology_weight"].tolist()):
        draw.ellipse((point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5), fill="#1b6ca8")
        draw.text((point[0] + 8, point[1] - 12), f"w={weight:.2f}", fill="black")
    image.save(output_path)


def save_summary_json(summary: dict[str, object], output_path: Path) -> None:
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def export_extension_tables(
    parameters: ReservoirParameters,
    frontier_records: list[dict[str, float]],
    uncertainty_records: list[dict[str, float | str]],
    algorithm_records: list[dict[str, float | str | bool]],
    rolling_horizon: dict[str, object],
    project_root: Path,
) -> None:
    frontier = pd.DataFrame(frontier_records)
    frontier.to_csv(project_root / "results" / "pareto_frontier.csv", index=False)
    pd.DataFrame(uncertainty_records).to_csv(project_root / "results" / "uncertainty_analysis.csv", index=False)
    pd.DataFrame(algorithm_records).to_csv(project_root / "results" / "algorithm_comparison.csv", index=False)

    rolling = pd.DataFrame(
        {
            "day": range(1, parameters.num_days + 1),
            "actual_inflow_m3s": list(parameters.rolling_horizon_actual_inflow_m3s),
            "release_m3s": list(rolling_horizon["releases_m3s"]),
            "storage_end_m3": list(rolling_horizon["storage_m3"])[1:],
        }
    )
    rolling.to_csv(project_root / "results" / "rolling_horizon_schedule.csv", index=False)
