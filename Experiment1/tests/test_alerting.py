from pathlib import Path

from src.alerting import check_alert, log_alert
from src.weather_api import parse_rainfall


def test_check_alert_thresholds() -> None:
    assert check_alert(9.99).level == "Green"
    assert check_alert(10).level == "Yellow"
    assert check_alert(19.99).level == "Yellow"
    assert check_alert(20).level == "Red"


def test_parse_rainfall_prefers_one_hour_data() -> None:
    payload = {"rain": {"1h": 12.5, "3h": 24.0}}
    assert parse_rainfall(payload) == 12.5


def test_log_alert_writes_file(tmp_path: Path) -> None:
    log_file = tmp_path / "alert_log.txt"
    log_alert("Beijing", 20.5, "Red", log_file)
    content = log_file.read_text(encoding="utf-8")
    assert "city=Beijing" in content
    assert "level=Red" in content
