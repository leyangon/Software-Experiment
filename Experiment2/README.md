# Experiment 2: SCS-CN Runoff Calculation

This project completes the required tasks in `Experiment2_SCSCN_Runoff` and also implements all optional extensions in a self-contained way.

## Project Structure

```text
Experiment2/
├── .venv/
├── data/
│   └── sample_hyetograph.csv
├── results/
│   ├── .gitkeep
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

## Features

- Correct SCS-CN runoff implementation with strict physical boundary handling
- AMC I, AMC II, and AMC III support
- Time-area routing extension
- Rational method comparison extension
- Interactive HTML runoff explorer with sliders
- Automated sensitivity analysis outputs and plot generation
- Test suite covering boundary conditions and physical correctness
- Report generation in Markdown, HTML, and DOCX

## Environment Setup

The project is designed to run with Python 3.10 or later. A virtual environment can be created with:

```bash
cd /Users/leyangon/Desktop/Experiments/Experiment2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

Generate all analysis outputs:

```bash
.venv/bin/python sensitivity_analysis.py
```

Run tests:

```bash
.venv/bin/python -m unittest -v test_scscn.py
```

Generate the report files:

```bash
.venv/bin/python create_report.py
```

## Notes

- The plot renderer tries `matplotlib` first. If it is unavailable, it falls back to a Pillow-based renderer so the experiment remains runnable offline.
- The generated outputs are written to `results/` and `runoff_comparison.png`.
