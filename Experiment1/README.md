# Experiment 1: Rainfall Forecasting and Alert System

This project implements the complete requirements of `Experiment1_Rainfall_Alert`, including OpenWeatherMap API integration, threshold-based alerting, Streamlit dashboard visualization, alert logging, prompt logging, and all optional extensions requested in the guide.

## Project Structure

```text
Experiment1/
├── .venv/
├── alert_log.txt
├── data/
│   └── sample_weather.json
├── prompt_log.md
├── requirements.txt
├── results/
├── screenshots/
├── src/
│   ├── alerting.py
│   ├── analytics.py
│   ├── config.py
│   └── weather_api.py
├── tests/
│   └── test_alerting.py
└── weather_monitor.py
```

## Features

- Real-time weather retrieval through OpenWeatherMap
- Graceful fallback to bundled sample data when API access is unavailable
- Threshold-based alerts:
  - Green: rainfall < 10 mm/h
  - Yellow: 10 <= rainfall < 20 mm/h
  - Red: rainfall >= 20 mm/h
- Automatic alert logging with timestamps
- Optional email notification for red alerts
- Streamlit dashboard with auto-refresh every 5 minutes
- Multi-city monitoring
- Historical rainfall trend chart
- Simple one-hour rainfall prediction based on recent history
- Folium map visualization

## Environment Setup

```bash
cd /Users/leyangon/Desktop/Experiments/Experiment1
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If you want live API data, configure:

```bash
export OPENWEATHER_API_KEY="your_api_key"
```

Optional email settings:

```bash
export RAIN_ALERT_EMAIL_ENABLED=true
export RAIN_ALERT_SMTP_SERVER="smtp.example.com"
export RAIN_ALERT_SMTP_PORT=587
export RAIN_ALERT_SMTP_USERNAME="your_username"
export RAIN_ALERT_SMTP_PASSWORD="your_password"
export RAIN_ALERT_SENDER="sender@example.com"
export RAIN_ALERT_RECIPIENT="recipient@example.com"
```

## Run the Dashboard

```bash
python -m streamlit run weather_monitor.py
```

## Test

```bash
python -m pytest
```

## Notes

- The bundled sample data allows offline demonstration and report screenshots even without an API key.
- `results/historical_rainfall.png` and `results/rainfall_map.html` are generated automatically when the dashboard runs.
