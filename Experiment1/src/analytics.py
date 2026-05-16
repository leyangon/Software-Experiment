"""History management, plotting, and lightweight forecasting."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import folium
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def initialize_history(cities: list[str]) -> pd.DataFrame:
    """Create a starter history table for supported cities."""

    rows = []
    now = datetime.now()
    for offset in range(6, 0, -1):
        timestamp = now - timedelta(hours=offset)
        for index, city in enumerate(cities):
            base = (index + 1) * 1.8
            seasonal = (offset % 3) * 1.1
            rows.append(
                {
                    "timestamp": timestamp,
                    "city": city,
                    "rainfall_mm_h": round(base + seasonal, 2),
                }
            )
    return pd.DataFrame(rows)


def append_history(history: pd.DataFrame, city: str, rainfall_mm_h: float) -> pd.DataFrame:
    """Append a new rainfall observation and return the updated frame."""

    new_row = pd.DataFrame(
        [{"timestamp": datetime.now(), "city": city, "rainfall_mm_h": rainfall_mm_h}]
    )
    updated = pd.concat([history, new_row], ignore_index=True)
    return updated.sort_values(["city", "timestamp"]).reset_index(drop=True)


def predict_next_hour(history: pd.DataFrame, city: str) -> float:
    """Predict the next-hour rainfall using a simple linear trend."""

    subset = history[history["city"] == city].tail(6).reset_index(drop=True)
    if subset.empty:
        return 0.0
    if len(subset) == 1:
        return float(subset.loc[0, "rainfall_mm_h"])

    x_values = np.arange(len(subset))
    y_values = subset["rainfall_mm_h"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x_values, y_values, 1)
    prediction = slope * len(subset) + intercept
    return round(max(prediction, 0.0), 2)


def save_history_chart(history: pd.DataFrame, output_path: Path) -> None:
    """Export the historical rainfall chart to disk."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(10, 5))
    for city, subset in history.groupby("city"):
        axis.plot(subset["timestamp"], subset["rainfall_mm_h"], marker="o", label=city)

    axis.set_title("Historical Rainfall Intensity")
    axis.set_xlabel("Time")
    axis.set_ylabel("Rainfall (mm/h)")
    axis.grid(True, alpha=0.3)
    axis.legend()
    figure.autofmt_xdate()
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def build_rainfall_map(records: list[dict], output_path: Path) -> folium.Map:
    """Create a Folium map for current city rainfall observations."""

    if not records:
        map_object = folium.Map(location=[39.9, 116.4], zoom_start=5)
    else:
        avg_lat = sum(record["latitude"] for record in records) / len(records)
        avg_lon = sum(record["longitude"] for record in records) / len(records)
        map_object = folium.Map(location=[avg_lat, avg_lon], zoom_start=5)
        for record in records:
            popup = (
                f"{record['city']}: {record['rainfall_mm_h']:.2f} mm/h"
                f"<br>Status: {record['alert_level']}"
            )
            marker_color = {
                "Green": "green",
                "Yellow": "orange",
                "Red": "red",
            }[record["alert_level"]]
            folium.CircleMarker(
                location=[record["latitude"], record["longitude"]],
                radius=9,
                color=marker_color,
                fill=True,
                fill_opacity=0.85,
                popup=popup,
            ).add_to(map_object)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    map_object.save(str(output_path))
    return map_object
