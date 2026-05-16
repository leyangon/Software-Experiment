from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from scscn_runoff import (
    AMCLevel,
    build_runoff_profiles,
    build_sensitivity_table,
    calculate_runoff,
    physical_validation,
    rational_method_peak_discharge,
    route_runoff_time_area,
)

PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = PROJECT_ROOT / "results"
PLOT_PATH = PROJECT_ROOT / "runoff_comparison.png"

CN_VALUES = [60, 70, 80, 90, 95, 100]
RAINFALL_FOR_CN_ANALYSIS = 50.0
PROFILE_RAINFALLS = list(range(0, 121, 5))


def _nice_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("Helvetica.ttc", size=size)
    except OSError:
        return ImageFont.load_default()


def _draw_axes(draw: ImageDraw.ImageDraw, origin: tuple[int, int], width: int, height: int) -> None:
    x0, y0 = origin
    draw.line((x0, y0, x0 + width, y0), fill="#333333", width=2)
    draw.line((x0, y0, x0, y0 - height), fill="#333333", width=2)


def _draw_line_plot(
    draw: ImageDraw.ImageDraw,
    values: list[tuple[float, float]],
    bounds: tuple[float, float, float, float],
    origin: tuple[int, int],
    width: int,
    height: int,
    color: str,
) -> None:
    min_x, max_x, min_y, max_y = bounds
    scaled = []
    for x_value, y_value in values:
        x = origin[0] + ((x_value - min_x) / (max_x - min_x)) * width
        y = origin[1] - ((y_value - min_y) / (max_y - min_y)) * height
        scaled.append((x, y))
    if len(scaled) > 1:
        draw.line(scaled, fill=color, width=3)
    for x, y in scaled:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)


def _render_plot_with_pillow(sensitivity_df: pd.DataFrame, profiles_df: pd.DataFrame, output_path: Path) -> None:
    image = Image.new("RGB", (1400, 700), "#ffffff")
    draw = ImageDraw.Draw(image)
    title_font = _nice_font(24)
    body_font = _nice_font(16)
    small_font = _nice_font(14)

    draw.text((40, 24), "SCS-CN Sensitivity Analysis", fill="#111111", font=title_font)
    draw.text((40, 58), "Left: CN vs runoff at P = 50 mm    Right: rainfall-runoff profiles", fill="#555555", font=body_font)

    left_origin = (90, 620)
    right_origin = (760, 620)
    chart_width = 500
    chart_height = 500
    _draw_axes(draw, left_origin, chart_width, chart_height)
    _draw_axes(draw, right_origin, chart_width, chart_height)

    left_points = [(float(row.curve_number), float(row.runoff_mm)) for row in sensitivity_df.itertuples()]
    _draw_line_plot(
        draw,
        left_points,
        bounds=(60.0, 100.0, 0.0, max(50.0, float(sensitivity_df["runoff_mm"].max()) + 5.0)),
        origin=left_origin,
        width=chart_width,
        height=chart_height,
        color="#005f73",
    )
    draw.text((200, 645), "Curve Number", fill="#333333", font=body_font)
    draw.text((20, 100), "Runoff (mm)", fill="#333333", font=body_font)

    colors = ["#9b2226", "#bb3e03", "#ca6702", "#0a9396", "#005f73", "#3a86ff"]
    max_y = max(50.0, float(profiles_df["runoff_mm"].max()) + 5.0)
    for color, cn in zip(colors, CN_VALUES):
        subset = profiles_df.loc[profiles_df["curve_number"] == cn]
        points = [(float(row.rainfall_mm), float(row.runoff_mm)) for row in subset.itertuples()]
        _draw_line_plot(
            draw,
            points,
            bounds=(0.0, 120.0, 0.0, max_y),
            origin=right_origin,
            width=chart_width,
            height=chart_height,
            color=color,
        )

    draw.text((910, 645), "Rainfall (mm)", fill="#333333", font=body_font)
    draw.text((685, 100), "Runoff (mm)", fill="#333333", font=body_font)

    legend_x = 1090
    legend_y = 120
    for index, cn in enumerate(CN_VALUES):
        y = legend_y + index * 28
        draw.rectangle((legend_x, y, legend_x + 18, y + 18), fill=colors[index])
        draw.text((legend_x + 26, y - 2), f"CN = {cn}", fill="#222222", font=small_font)

    image.save(output_path)


def _render_plot_with_matplotlib(sensitivity_df: pd.DataFrame, profiles_df: pd.DataFrame, output_path: Path) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        return False

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    axes[0].plot(sensitivity_df["curve_number"], sensitivity_df["runoff_mm"], marker="o", linewidth=2)
    axes[0].set_title("CN vs Runoff at P = 50 mm")
    axes[0].set_xlabel("Curve Number")
    axes[0].set_ylabel("Runoff (mm)")
    axes[0].grid(True, alpha=0.3)

    for cn in CN_VALUES:
        subset = profiles_df.loc[profiles_df["curve_number"] == cn]
        axes[1].plot(subset["rainfall_mm"], subset["runoff_mm"], label=f"CN={cn}", linewidth=2)
    axes[1].set_title("Rainfall vs Runoff for Different CN Values")
    axes[1].set_xlabel("Rainfall (mm)")
    axes[1].set_ylabel("Runoff (mm)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    return True


def save_plot(sensitivity_df: pd.DataFrame, profiles_df: pd.DataFrame, output_path: Path) -> str:
    if _render_plot_with_matplotlib(sensitivity_df, profiles_df, output_path):
        return "matplotlib"
    _render_plot_with_pillow(sensitivity_df, profiles_df, output_path)
    return "pillow"


def save_interactive_html(curve_numbers: Iterable[int], output_path: Path) -> None:
    options = "".join(f'<option value="{cn}">{cn}</option>' for cn in curve_numbers)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>SCS-CN Interactive Explorer</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; background: #f7fbfc; color: #102a43; }}
    .panel {{ max-width: 860px; background: white; padding: 1.5rem 1.75rem; border-radius: 16px; box-shadow: 0 10px 30px rgba(16,42,67,0.08); }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    label {{ font-weight: 600; display: block; margin-bottom: 0.4rem; }}
    input, select {{ width: 100%; }}
    .result {{ margin-top: 1.5rem; padding: 1rem; background: #eef6f6; border-radius: 12px; }}
  </style>
</head>
<body>
  <div class="panel">
    <h1>SCS-CN Interactive Explorer</h1>
    <p>Optional extension: adjust rainfall, curve number, and AMC to inspect runoff response interactively.</p>
    <div class="grid">
      <div>
        <label for="rainfall">Rainfall (mm)</label>
        <input id="rainfall" type="range" min="0" max="150" step="1" value="50">
        <p id="rainfallLabel">50 mm</p>
      </div>
      <div>
        <label for="cn">Curve Number</label>
        <select id="cn">{options}</select>
      </div>
      <div>
        <label for="amc">AMC</label>
        <select id="amc">
          <option value="I">I</option>
          <option value="II" selected>II</option>
          <option value="III">III</option>
        </select>
      </div>
    </div>
    <div class="result" id="resultBox"></div>
  </div>
  <script>
    function adjustCN(cn, amc) {{
      if (cn <= 0) return 0;
      if (cn >= 100) return 100;
      if (amc === 'II') return cn;
      if (amc === 'I') return cn / (2.281 - 0.01281 * cn);
      return cn / (0.427 + 0.00573 * cn);
    }}
    function runoff(P, cn, amc) {{
      const adj = adjustCN(cn, amc);
      if (adj <= 0) return 0;
      if (adj >= 100) return P;
      const S = 25400 / adj - 254;
      const Ia = 0.2 * S;
      if (P <= Ia) return 0;
      const Q = Math.pow(P - Ia, 2) / (P - Ia + S);
      return Math.max(0, Math.min(P, Q));
    }}
    function update() {{
      const P = Number(document.getElementById('rainfall').value);
      const cn = Number(document.getElementById('cn').value);
      const amc = document.getElementById('amc').value;
      document.getElementById('rainfallLabel').textContent = `${{P}} mm`;
      const q = runoff(P, cn, amc);
      document.getElementById('resultBox').innerHTML = `
        <strong>Calculated runoff:</strong> ${{q.toFixed(3)}} mm<br>
        <strong>Runoff ratio:</strong> ${{P === 0 ? 0 : (q / P).toFixed(3)}}<br>
        <strong>Physical check:</strong> Q ≤ P is ${{q <= P ? 'satisfied' : 'violated'}}
      `;
    }}
    ['rainfall', 'cn', 'amc'].forEach(id => document.getElementById(id).addEventListener('input', update));
    update();
  </script>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def create_optional_outputs(profiles_df: pd.DataFrame) -> None:
    amc_rows = []
    for amc in ("I", "II", "III"):
        for cn in CN_VALUES:
            runoff = float(calculate_runoff(RAINFALL_FOR_CN_ANALYSIS, cn, amc=amc))  # type: ignore[arg-type]
            amc_rows.append({"amc": amc, "curve_number": cn, "rainfall_mm": RAINFALL_FOR_CN_ANALYSIS, "runoff_mm": runoff})
    pd.DataFrame(amc_rows).to_csv(RESULTS_DIR / "amc_comparison.csv", index=False)

    time_area_weights = [0.10, 0.20, 0.35, 0.20, 0.10, 0.05]
    hyetograph = pd.read_csv(PROJECT_ROOT / "data" / "sample_hyetograph.csv")
    routed = route_runoff_time_area(hyetograph["rainfall_mm"], time_area_weights)
    routed_df = hyetograph.copy()
    routed_df["routed_runoff_mm"] = routed
    routed_df.to_csv(RESULTS_DIR / "time_area_routing.csv", index=False)

    rational_rows = []
    for cn in CN_VALUES:
        runoff_depth = float(calculate_runoff(RAINFALL_FOR_CN_ANALYSIS, cn))
        runoff_coefficient = min(0.98, max(0.05, runoff_depth / RAINFALL_FOR_CN_ANALYSIS if RAINFALL_FOR_CN_ANALYSIS else 0.0))
        peak_discharge = rational_method_peak_discharge(runoff_coefficient, 40.0, 25.0)
        rational_rows.append(
            {
                "curve_number": cn,
                "rainfall_mm": RAINFALL_FOR_CN_ANALYSIS,
                "scs_cn_runoff_mm": runoff_depth,
                "derived_runoff_coefficient": runoff_coefficient,
                "rational_peak_discharge_m3s": peak_discharge,
            }
        )
    pd.DataFrame(rational_rows).to_csv(RESULTS_DIR / "rational_method_comparison.csv", index=False)


def write_observations(sensitivity_df: pd.DataFrame, validation: dict[str, bool], renderer: str) -> None:
    observations = [
        "1. For fixed rainfall of 50 mm, runoff increases monotonically as CN increases from 60 to 100.",
        "2. CN = 100 produces runoff equal to rainfall, which matches the impervious-surface boundary condition.",
        "3. Lower CN values preserve more storage capacity, so runoff starts later and grows more slowly.",
        f"4. Physical validation status: Q<=P={validation['q_leq_p']}, monotonic_CN={validation['monotonic_cn']}, zero_rainfall={validation['zero_rainfall']}.",
        f"5. Plot renderer used in this environment: {renderer}.",
        "6. AMC III produces more runoff than AMC II, while AMC I produces less, which is physically consistent.",
    ]
    (RESULTS_DIR / "sensitivity_observations.txt").write_text("\n".join(observations), encoding="utf-8")


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    sensitivity_df = build_sensitivity_table(RAINFALL_FOR_CN_ANALYSIS, CN_VALUES)
    profiles_df = build_runoff_profiles(PROFILE_RAINFALLS, CN_VALUES)

    sensitivity_df.to_csv(RESULTS_DIR / "cn_sensitivity.csv", index=False)
    profiles_df.to_csv(RESULTS_DIR / "rainfall_runoff_profiles.csv", index=False)

    renderer = save_plot(sensitivity_df, profiles_df, PLOT_PATH)
    create_optional_outputs(profiles_df)
    save_interactive_html(CN_VALUES, RESULTS_DIR / "interactive_runoff_explorer.html")

    validation = physical_validation(PROFILE_RAINFALLS, CN_VALUES)
    write_observations(sensitivity_df, validation, renderer)

    print("Generated:")
    print(f"- {PLOT_PATH}")
    print(f"- {RESULTS_DIR / 'cn_sensitivity.csv'}")
    print(f"- {RESULTS_DIR / 'rainfall_runoff_profiles.csv'}")
    print(f"- {RESULTS_DIR / 'amc_comparison.csv'}")
    print(f"- {RESULTS_DIR / 'time_area_routing.csv'}")
    print(f"- {RESULTS_DIR / 'rational_method_comparison.csv'}")
    print(f"- {RESULTS_DIR / 'interactive_runoff_explorer.html'}")


if __name__ == "__main__":
    main()
