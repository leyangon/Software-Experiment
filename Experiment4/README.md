# Experiment 4: Flood Inundation Analysis

This project completes the specialized experiment `Experiment4_Flood_Inundation` and includes all optional extensions in an offline-runnable form.

## Project Structure

```text
Experiment4/
├── .venv/
├── data/
├── results/
├── src/
├── tests/
├── Experiment4_Report.docx
├── Experiment4_Report.html
├── Experiment4_Report.md
├── README.md
├── create_report.py
├── dem_data.npy
├── flood_curve.png
├── flood_extent_40m.png
├── flood_extent_50m.png
├── flood_inundation.py
├── prompt_log.md
└── validation_report.txt
```

## Environment Setup

```bash
cd /Users/leyangon/Desktop/Experiments/Experiment4
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python flood_inundation.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python create_report.py
```

## Optional Extensions Implemented

- Offline loading and normalization of a real DEM sample derived from the Matplotlib `jacksboro_fault_dem` dataset
- Flood routing based on 4-neighbour connectivity from an inflow boundary
- Building-footprint barriers that block inundation spread
- Animated GIF of rising water levels
- Flood volume calculation across all simulated water levels
