"""OpenWeatherMap client and local fallback sample loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


API_URL = "https://api.openweathermap.org/data/2.5/weather"


def parse_rainfall(payload: dict[str, Any]) -> float:
    """Extract rainfall intensity in mm/h from the API payload."""

    rain = payload.get("rain", {})
    if "1h" in rain:
        return float(rain["1h"])
    if "3h" in rain:
        return float(rain["3h"]) / 3.0
    snow = payload.get("snow", {})
    if "1h" in snow:
        return float(snow["1h"])
    if "3h" in snow:
        return float(snow["3h"]) / 3.0
    return 0.0


def fetch_weather(city: str, api_key: str, units: str = "metric", timeout: int = 15) -> dict[str, Any]:
    """Fetch current weather data from OpenWeatherMap."""

    import requests

    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY is not configured.")

    response = requests.get(
        API_URL,
        params={"q": city, "appid": api_key, "units": units},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    rainfall = parse_rainfall(payload)
    weather_summary = payload.get("weather", [{}])[0].get("description", "unknown")
    return {
        "city": payload.get("name", city),
        "country": payload.get("sys", {}).get("country", ""),
        "rainfall_mm_h": rainfall,
        "temperature_c": float(payload.get("main", {}).get("temp", 0.0)),
        "humidity_pct": int(payload.get("main", {}).get("humidity", 0)),
        "weather": weather_summary,
        "longitude": float(payload.get("coord", {}).get("lon", 0.0)),
        "latitude": float(payload.get("coord", {}).get("lat", 0.0)),
        "source": "OpenWeatherMap",
    }


def load_sample_payloads(sample_path: Path) -> dict[str, dict[str, Any]]:
    """Load bundled sample payloads for offline testing and demos."""

    with sample_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_weather_with_fallback(
    city: str,
    api_key: str,
    sample_path: Path,
    units: str = "metric",
) -> tuple[dict[str, Any], str]:
    """Try live API data first, then fall back to local sample data."""

    try:
        return fetch_weather(city, api_key, units=units), ""
    except Exception as exc:
        payloads = load_sample_payloads(sample_path)
        sample = payloads.get(city)
        if sample is None:
            available = ", ".join(sorted(payloads))
            raise RuntimeError(
                f"Unable to fetch data for {city} and no sample exists. Available samples: {available}"
            ) from exc
        sample = dict(sample)
        sample["source"] = "sample_data"
        return sample, str(exc)
