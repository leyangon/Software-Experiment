Software Development
实验报告
使用 OpenAI Codex
辅助完成 SCS-CN 产流计算实验

姓名
刘子康
班级
S4280
学号
3124358273
Email
leyangon@qq.com
日期
2026-04-21

## Abstract

This experiment implemented the Soil Conservation Service Curve Number (SCS-CN) runoff calculation method according to the guide `Experiment2_SCSCN_Runoff`. The final project translates the hydrological formula into Python code, handles all key physical boundary conditions, and performs sensitivity analysis for different curve number values. To make the project stable in an offline laboratory environment, the implementation was designed to run without relying on network access and includes a built-in fallback plot renderer. The required deliverables were completed, including the main runoff implementation, a comprehensive test suite, a sensitivity analysis script, a generated runoff comparison figure, and a prompt log documenting AI-assisted development. In addition, all optional extensions were implemented: antecedent moisture condition adjustment, time-area routing, an interactive HTML explorer with sliders for rainfall and curve number, and a comparison with the Rational method. Validation confirmed that runoff remains zero when rainfall does not exceed initial abstraction, that runoff never exceeds rainfall, and that higher curve number values consistently produce greater runoff. The experiment shows that AI can accelerate formula translation and code scaffolding, but physically correct results still depend on manual review, edge-case testing, and hydrological reasoning.

## 1 Experimental Objectives

The goal of this experiment was to implement and validate the SCS-CN runoff calculation model in a form that is mathematically correct, physically consistent, and suitable for engineering-style analysis.

The specific objectives were as follows:

- To translate the SCS-CN runoff formula into a reliable Python implementation.
- To handle physical boundary conditions such as `P < Ia`, `CN = 0`, and `CN = 100`.
- To verify the implementation through a complete and reproducible test suite.
- To perform sensitivity analysis for different curve number values under fixed rainfall conditions.
- To visualize the runoff response and summarize the observed hydrological relationship.
- To complete optional extensions that broaden the analysis beyond the minimum requirements.
- To document how AI support was used and where human correction remained necessary.

## 2 Experimental Process

### 2.1 Task Description

According to the experiment guide, the work needed to cover four parts: formula implementation, boundary-condition testing, sensitivity analysis, and validation with documentation. The required deliverables were `scscn_runoff.py`, `test_scscn.py`, `sensitivity_analysis.py`, `runoff_comparison.png`, and `prompt_log.md`. The optional extensions listed in the guide were also implemented in this project.

The final project was stored in:

`/Users/leyangon/Desktop/Experiments/Experiment2`

### 2.2 Environment Setup and Project Structure

The project was developed for Python 3.10+ and deployed in a dedicated virtual environment created under the experiment directory. Because the current local runtime already provides the required scientific packages offline, the environment was created with the `--system-site-packages` option so that the project remains fully runnable without external downloads.

The project structure is shown below:

```text
Experiment2/
├── .venv/
├── data/
│   └── sample_hyetograph.csv
├── results/
│   ├── amc_comparison.csv
│   ├── cn_sensitivity.csv
│   ├── interactive_runoff_explorer.html
│   ├── rainfall_runoff_profiles.csv
│   ├── rational_method_comparison.csv
│   ├── sensitivity_observations.txt
│   └── time_area_routing.csv
├── Experiment2_Report.docx
├── Experiment2_Report.html
├── Experiment2_Report.md
├── create_report.py
├── prompt_log.md
├── requirements.txt
├── runoff_comparison.png
├── scscn_runoff.py
├── sensitivity_analysis.py
└── test_scscn.py
```

This structure keeps the experiment compact while still separating modeling logic, analysis generation, output files, and report artifacts.

### 2.3 Formula Implementation

The core implementation is placed in `scscn_runoff.py`. The main function `calculate_runoff()` follows the SCS-CN equations:

- `S = (25400 / CN) - 254`
- `Ia = 0.2 * S`
- `Q = 0` when `P <= Ia`
- `Q = (P - Ia)^2 / (P - Ia + S)` when `P > Ia`

Several safeguards were added to ensure physical correctness. If `CN <= 0`, the function returns zero runoff because the case represents complete infiltration and also avoids division by zero. If `CN >= 100`, runoff is set equal to rainfall to represent an impervious surface. Negative rainfall input is clipped to zero. Finally, the computed runoff is clipped so that `0 <= Q <= P` always holds.

To improve usability, the implementation supports both scalar rainfall input and vectorized rainfall sequences. This makes the same function suitable for single-case verification and profile generation during sensitivity analysis.

### 2.4 Boundary Condition Testing

The test suite is implemented in `test_scscn.py`. It covers all required boundary conditions from the guide:

- `P = 0`, where runoff must be zero;
- `P < Ia`, where runoff must be zero;
- `P = Ia`, where runoff must still be zero;
- the normal example `P = 50 mm`, `CN = 80`, where runoff is approximately `13.8 mm`;
- `CN = 100`, which should produce maximum runoff equal to rainfall;
- the physical condition `Q <= P` for a range of test values.

The final test suite also includes extra checks for monotonic runoff increase with increasing CN, physically ordered AMC adjustments, and non-negative time-area routing output. These extra checks strengthen confidence in both the required implementation and the optional extensions.

### 2.5 Sensitivity Analysis and Visualization

The sensitivity analysis is implemented in `sensitivity_analysis.py`. First, the rainfall depth was fixed at `P = 50 mm`, and runoff was calculated for `CN = [60, 70, 80, 90, 95, 100]`. Second, rainfall-runoff profiles were generated for rainfall values from `0 mm` to `120 mm` across the same CN set.

The guide requires a generated comparison figure. The script therefore attempts to use `matplotlib` when available, but in this local offline environment a Pillow-based renderer is also provided as a fallback. This guarantees that `runoff_comparison.png` can still be produced without adding fragile external dependencies. The generated figure contains:

- a line plot of curve number versus runoff at fixed rainfall;
- a comparison plot of rainfall versus runoff for different curve numbers.

The sensitivity output tables are also saved to `results/cn_sensitivity.csv` and `results/rainfall_runoff_profiles.csv` for direct inspection.

### 2.6 Optional Extensions

All optional extensions listed in the guide were completed.

First, antecedent moisture condition adjustment was implemented. The project supports AMC I, AMC II, and AMC III using standard CN transformation equations. This makes it possible to explore how drier or wetter initial watershed conditions influence runoff.

Second, a time-area routing extension was added. A sample hyetograph is read from `data/sample_hyetograph.csv`, and routed runoff is produced through a normalized weighting curve. The output is saved to `results/time_area_routing.csv`.

Third, an interactive explorer was created as `results/interactive_runoff_explorer.html`. It provides sliders and selectors for rainfall depth, curve number, and AMC. This satisfies the requirement for an interactive plot-like extension while keeping the project lightweight and browser-friendly.

Fourth, the SCS-CN result was compared with the Rational method. A derived runoff coefficient based on the computed runoff ratio was used to estimate peak discharge for a representative catchment. The comparison output is stored in `results/rational_method_comparison.csv`.

### 2.7 Validation and Documentation

Validation focused on both numerical correctness and physical consistency. The implemented checks confirmed the following:

- runoff remains zero when rainfall does not exceed initial abstraction;
- runoff never exceeds rainfall;
- higher curve number values produce more runoff under the same rainfall;
- AMC III produces more runoff than AMC II, while AMC I produces less;
- the `CN = 100` boundary produces runoff equal to rainfall.

The executed test command was:

```bash
.venv/bin/python -m unittest -v test_scscn.py
```

The result was:

```text
11 tests passed
```

The prompt log was also updated to record the AI interactions used for formula drafting, testing support, sensitivity analysis, and extension design. Importantly, the final implementation was not accepted without review. Human inspection corrected likely AI mistakes, especially around `CN = 0`, dependency assumptions for plotting, and preservation of the `Q <= P` physical constraint.

## 3 Results and Analysis

### 3.1 Functional Completion

All mandatory deliverables were completed successfully. The project includes the required runoff calculation program, a full test suite, a sensitivity analysis script, the generated PNG comparison figure, and the prompt log. In addition, every optional extension from the guide was completed rather than omitted.

### 3.2 Hydrological Interpretation

The generated results show a clear and physically meaningful pattern. For a fixed rainfall event, runoff depth increases as curve number increases. This is expected because higher curve number values correspond to lower watershed storage capacity and greater runoff potential. The example `P = 50 mm`, `CN = 80` produced a runoff depth close to `13.8 mm`, which matches the reference calculation in the guide.

The rainfall-runoff profile curves also show that low-CN watersheds require more rainfall before appreciable runoff begins, while high-CN surfaces respond quickly and strongly. At the extreme case `CN = 100`, runoff equals rainfall, which is consistent with an impervious surface assumption.

### 3.3 Role of AI Assistance

AI assistance was helpful for quickly drafting the formula structure, proposing test cases, and outlining optional extensions. However, the final quality depended on careful human review. Several points required explicit correction or strengthening:

- guarding against division by zero when `CN = 0`;
- handling `CN = 100` as a special physical case;
- ensuring that `Q` never exceeds `P`;
- providing a local rendering fallback when `matplotlib` is unavailable;
- checking that optional extension outputs remain physically reasonable.

This confirms that AI can improve development speed, but hydrological correctness and engineering reliability still depend on manual validation.

## 4 Summary

This experiment successfully completed the implementation and validation of the SCS-CN runoff calculation method required by `Experiment2_SCSCN_Runoff`. The final program correctly translates the formula into Python, handles boundary conditions, verifies physical correctness with tests, and performs the required sensitivity analysis. It also extends the base task with AMC adjustment, time-area routing, an interactive exploration page, and comparison with the Rational method.

Through this experiment, I gained a more concrete understanding of how hydrological formulas are translated into software, how physical constraints guide code review, and how AI can accelerate development without replacing engineering judgment. Overall, the project satisfies the stated experimental objectives and provides a complete, reproducible, and well-documented submission.
