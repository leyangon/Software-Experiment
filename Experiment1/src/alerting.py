"""Threshold checks, logging, and notification helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
import smtplib

from .config import EmailSettings


@dataclass
class AlertResult:
    level: str
    color: str
    description: str
    triggered: bool


def check_alert(rainfall_mm_per_hour: float) -> AlertResult:
    """Classify rainfall intensity according to the experiment thresholds."""

    if rainfall_mm_per_hour < 10:
        return AlertResult(
            level="Green",
            color="#2E8B57",
            description="Normal rainfall conditions.",
            triggered=False,
        )
    if rainfall_mm_per_hour < 20:
        return AlertResult(
            level="Yellow",
            color="#DAA520",
            description="Moderate rainfall. Stay prepared.",
            triggered=False,
        )
    return AlertResult(
        level="Red",
        color="#C0392B",
        description="Heavy rainfall detected. Alert conditions reached.",
        triggered=True,
    )


def log_alert(city: str, rainfall_mm_per_hour: float, level: str, log_path: Path) -> None:
    """Append alert records to the text log with an ISO timestamp."""

    timestamp = datetime.now().isoformat(timespec="seconds")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{timestamp} | city={city} | rainfall_mm_h={rainfall_mm_per_hour:.2f} | level={level}\n"
        )


def send_email_alert(
    city: str,
    rainfall_mm_per_hour: float,
    settings: EmailSettings,
) -> tuple[bool, str]:
    """Send an email alert if SMTP settings are configured."""

    required_fields = [
        settings.smtp_server,
        settings.username,
        settings.password,
        settings.sender,
        settings.recipient,
    ]
    if not settings.enabled:
        return False, "Email notifications are disabled."
    if not all(required_fields):
        return False, "Email settings are incomplete, so notification was skipped."

    message = EmailMessage()
    message["Subject"] = f"Rainfall Alert for {city}"
    message["From"] = settings.sender
    message["To"] = settings.recipient
    message.set_content(
        "Heavy rainfall detected.\n\n"
        f"City: {city}\n"
        f"Rainfall intensity: {rainfall_mm_per_hour:.2f} mm/h\n"
        f"Time: {datetime.now().isoformat(timespec='seconds')}\n"
    )

    try:
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port, timeout=15) as server:
            server.starttls()
            server.login(settings.username, settings.password)
            server.send_message(message)
    except Exception as exc:  # pragma: no cover - network and credential dependent
        return False, f"Email notification failed: {exc}"

    return True, "Email alert sent successfully."
