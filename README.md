# Smart Water Lab Experiments

This repository contains four Python-based hydrology and water resources experiments completed for the Smart Water Lab software development assignment.

## Author

- Name: 刘子康
- Class: S4280
- Student ID: 3124358273
- Email: leyangon@qq.com

## Repository Structure

```text
Experiment1/  Short-term rainfall monitoring and alert dashboard
Experiment2/  SCS-CN runoff calculation and sensitivity analysis
Experiment3/  Reservoir release optimization and trade-off analysis
Experiment4/  DEM-based flood inundation simulation
```

The repository is kept close to the guide Deliverables. A few support modules are included where the implementation is modular, so the delivered scripts can still run directly.

## Deliverable Checklist

### Experiment 1: Rainfall Alert System

- `Experiment1/weather_monitor.py`
- `Experiment1/alert_log.txt`
- `Experiment1/prompt_log.md`
- `Experiment1/screenshots/dashboard_preview.png`

Support files:

- `Experiment1/src/*.py`
- `Experiment1/data/sample_weather.json`
- `Experiment1/requirements.txt`
- `Experiment1/tests/*.py`

### Experiment 2: SCS-CN Runoff Calculation

- `Experiment2/scscn_runoff.py`
- `Experiment2/test_scscn.py`
- `Experiment2/sensitivity_analysis.py`
- `Experiment2/runoff_comparison.png`
- `Experiment2/prompt_log.md`

Support file:

- `Experiment2/data/sample_hyetograph.csv`
- `Experiment2/requirements.txt`

### Experiment 3: Reservoir Optimization

- `Experiment3/reservoir_optimize.py`
- `Experiment3/optimal_schedule.csv`
- `Experiment3/tradeoff_analysis.png`
- `Experiment3/prompt_log.md`
- `Experiment3/validation_report.txt`

Supplementary explanation:

- `Experiment3/formulation.md`
- `Experiment3/src/*.py`
- `Experiment3/requirements.txt`
- `Experiment3/tests/*.py`

### Experiment 4: Flood Inundation Analysis

- `Experiment4/flood_inundation.py`
- `Experiment4/dem_data.npy`
- `Experiment4/flood_extent_40m.png`
- `Experiment4/flood_extent_50m.png`
- `Experiment4/flood_curve.png`
- `Experiment4/prompt_log.md`

Supplementary validation:

- `Experiment4/validation_report.txt`
- `Experiment4/src/*.py`
- `Experiment4/requirements.txt`
- `Experiment4/tests/*.py`

## How to Verify

Run the deterministic tests and checks from the repository root:

```bash
cd Experiment2
python3 -m unittest -q

cd ../Experiment3
python3 -m unittest discover -s tests -p 'test*.py' -q

cd ../Experiment4
python3 -m unittest discover -s tests -p 'test*.py' -q
```

The local verification before upload passed:

- Experiment1 smoke test: OK
- Experiment2 unit tests: 11 passed
- Experiment3 unit tests: 6 passed
- Experiment4 unit tests: 5 passed

## Notes

- API keys and local virtual environments are intentionally not included.
- Generated reports and extended analysis outputs are kept locally but excluded from Git tracking to keep the submission focused on the guide Deliverables.
- The implementation uses offline sample data where appropriate so the experiments remain reproducible without network access.
