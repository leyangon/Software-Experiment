"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
DEFAULT_ALERT_LOG = PROJECT_ROOT / "alert_log.txt"
DEFAULT_PROMPT_LOG = PROJECT_ROOT / "prompt_log.md"


@dataclass
class EmailSettings:
    enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    sender: str = ""
    recipient: str = ""


@dataclass
class AppConfig:
    api_key: str = ""
    units: str = "metric"
    cities: list[str] = field(
        default_factory=lambda: ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"]
    )
    refresh_minutes: int = 5
    alert_log_path: Path = DEFAULT_ALERT_LOG
    sample_data_path: Path = DATA_DIR / "sample_weather.json"
    email: EmailSettings = field(default_factory=EmailSettings)


def load_config() -> AppConfig:
    """Load configuration from environment variables with safe defaults."""

    raw_cities = os.getenv("RAIN_MONITOR_CITIES")
    cities = (
        [city.strip() for city in raw_cities.split(",") if city.strip()]
        if raw_cities
        else ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"]
    )

    email_enabled = os.getenv("RAIN_ALERT_EMAIL_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    return AppConfig(
        api_key=os.getenv("OPENWEATHER_API_KEY", ""),
        units=os.getenv("OPENWEATHER_UNITS", "metric"),
        cities=cities,
        refresh_minutes=int(os.getenv("RAIN_REFRESH_MINUTES", "5")),
        email=EmailSettings(
            enabled=email_enabled,
            smtp_server=os.getenv("RAIN_ALERT_SMTP_SERVER", ""),
            smtp_port=int(os.getenv("RAIN_ALERT_SMTP_PORT", "587")),
            username=os.getenv("RAIN_ALERT_SMTP_USERNAME", ""),
            password=os.getenv("RAIN_ALERT_SMTP_PASSWORD", ""),
            sender=os.getenv("RAIN_ALERT_SENDER", ""),
            recipient=os.getenv("RAIN_ALERT_RECIPIENT", ""),
        ),
    )
