# Experiment 3: Reservoir Optimization

This project completes the specialized experiment `Experiment3_Reservoir_Optimization` and includes all optional extensions.

## Project Structure

```text
Experiment3/
├── .venv/
├── data/
├── results/
│   ├── algorithm_comparison.csv
│   ├── pareto_frontier.csv
│   ├── rolling_horizon_schedule.csv
│   ├── summary.json
│   ├── uncertainty_analysis.csv
│   └── water_quality_schedule.csv
├── src/
│   ├── analysis.py
│   ├── config.py
│   └── optimization.py
├── tests/
│   └── test_reservoir.py
├── Experiment3_Report.docx
├── Experiment3_Report.html
├── Experiment3_Report.md
├── README.md
├── create_report.py
├── optimal_schedule.csv
├── prompt_log.md
├── requirements.txt
├── reservoir_optimize.py
├── tradeoff_analysis.png
└── validation_report.txt
```

## Environment Setup

```bash
cd /Users/leyangon/Desktop/Experiments/Experiment3
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python reservoir_optimize.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python create_report.py
```

## Implemented Extensions

- Inflow uncertainty analysis using multiple forecast scenarios
- Rolling horizon dispatch with updated daily inflow observations
- Water-quality-aware constraints on storage and release ramping
- Algorithm comparison between SLSQP and L-BFGS-B
