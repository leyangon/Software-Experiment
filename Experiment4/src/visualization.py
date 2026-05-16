from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from .flood import FloodResult


def _style_axes(ax, title: str) -> None:
    ax.set_title(title)
    ax.set_xticks([])
    ax.set_yticks([])


def save_flood_figure(
    dem: np.ndarray,
    result: FloodResult,
    output_path: Path,
    *,
    barrier_mask: np.ndarray | None = None,
    suptitle: str | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), constrained_layout=True)

    im0 = axes[0].imshow(dem, cmap="gray")
    _style_axes(axes[0], "Original DEM")
    fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04, label="Elevation (m)")

    axes[1].imshow(dem, cmap="gray")
    overlay = np.ma.masked_where(~result.flooded_mask, result.flooded_mask.astype(float))
    axes[1].imshow(overlay, cmap="Blues", alpha=0.7, vmin=0.0, vmax=1.0)
    if barrier_mask is not None:
        barrier_overlay = np.ma.masked_where(~barrier_mask, barrier_mask.astype(float))
        axes[1].imshow(barrier_overlay, cmap="Reds", alpha=0.35, vmin=0.0, vmax=1.0)
    _style_axes(axes[1], f"Flood Extent at {result.water_level_m:.0f} m")

    depth_overlay = np.ma.masked_where(result.depth_m <= 0.0, result.depth_m)
    im2 = axes[2].imshow(depth_overlay, cmap="Blues")
    _style_axes(axes[2], "Inundation Depth")
    fig.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04, label="Depth (m)")

    title = suptitle or (
        f"Flood Analysis | Water Level {result.water_level_m:.0f} m | "
        f"Flooded {result.flooded_percentage:.2f}% | Volume {result.flood_volume_m3:,.0f} m^3"
    )
    fig.suptitle(title, fontsize=13)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def save_multi_level_comparison(
    dem: np.ndarray,
    results: list[FloodResult],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(10, 9), constrained_layout=True)
    for ax, result in zip(axes.flat, results):
        ax.imshow(dem, cmap="gray")
        overlay = np.ma.masked_where(~result.flooded_mask, result.depth_m)
        im = ax.imshow(overlay, cmap="Blues", alpha=0.85)
        _style_axes(ax, f"{result.water_level_m:.0f} m | {result.flooded_percentage:.1f}%")
    fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.03, pad=0.02, label="Depth (m)")
    fig.suptitle("Side-by-Side Flood Comparison at Different Water Levels", fontsize=13)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def save_flood_curve(results: list[FloodResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    levels = [result.water_level_m for result in results]
    percentages = [result.flooded_percentage for result in results]
    volumes = [result.flood_volume_m3 / 1_000_000.0 for result in results]

    fig, ax1 = plt.subplots(figsize=(8.5, 5.2), constrained_layout=True)
    ax1.plot(levels, percentages, marker="o", color="#1f4e79", linewidth=2.0)
    ax1.set_xlabel("Water Level (m)")
    ax1.set_ylabel("Flooded Area (%)", color="#1f4e79")
    ax1.tick_params(axis="y", labelcolor="#1f4e79")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(levels, volumes, marker="s", color="#4f81bd", linestyle="--", linewidth=1.8)
    ax2.set_ylabel("Flood Volume (10^6 m^3)", color="#4f81bd")
    ax2.tick_params(axis="y", labelcolor="#4f81bd")

    plt.title("Water Level vs Flooded Percentage and Volume")
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _frame_from_result(dem: np.ndarray, result: FloodResult) -> Image.Image:
    norm = (dem - dem.min()) / max(dem.max() - dem.min(), 1e-9)
    gray = (norm * 255).astype(np.uint8)
    rgb = np.stack([gray, gray, gray], axis=-1)
    flooded = result.flooded_mask
    rgb[flooded, 0] = (0.35 * rgb[flooded, 0]).astype(np.uint8)
    rgb[flooded, 1] = (0.55 * rgb[flooded, 1]).astype(np.uint8)
    rgb[flooded, 2] = np.maximum(rgb[flooded, 2], 220)
    image = Image.fromarray(rgb)
    return image.resize((400, 400), resample=Image.Resampling.NEAREST)


def save_animation_gif(dem: np.ndarray, results: list[FloodResult], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames = [_frame_from_result(dem, result) for result in results]
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=500,
        loop=0,
    )
