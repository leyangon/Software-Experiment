"""Streamlit rainfall monitoring dashboard for the experiment."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_folium import st_folium

from src.alerting import check_alert, log_alert, send_email_alert
from src.analytics import (
    append_history,
    build_rainfall_map,
    initialize_history,
    predict_next_hour,
    save_history_chart,
)
from src.config import RESULTS_DIR, load_config
from src.weather_api import fetch_weather_with_fallback


st.set_page_config(page_title="Rainfall Monitor", page_icon="🌧️", layout="wide")

config = load_config()


def render_alert_card(city_record: dict) -> None:
    """Show a city status card with color-coded styling."""

    color = city_record["alert_color"]
    st.markdown(
        f"""
        <div style="padding: 1rem; border-radius: 12px; background-color: {color}; color: white;">
            <h4 style="margin: 0 0 0.5rem 0;">{city_record["city"]}</h4>
            <p style="font-size: 1.4rem; margin: 0;">{city_record["rainfall_mm_h"]:.2f} mm/h</p>
            <p style="margin: 0.4rem 0 0 0;">{city_record["alert_level"]} | {city_record["description"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_city_data(selected_cities: list[str]) -> tuple[list[dict], list[str]]:
    """Fetch rainfall data for each selected city."""

    records: list[dict] = []
    warnings: list[str] = []
    for city in selected_cities:
        weather, error_message = fetch_weather_with_fallback(
            city=city,
            api_key=config.api_key,
            sample_path=config.sample_data_path,
            units=config.units,
        )
        alert = check_alert(weather["rainfall_mm_h"])
        record = {
            **weather,
            "alert_level": alert.level,
            "alert_color": alert.color,
            "description": alert.description,
            "triggered": alert.triggered,
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if error_message:
            warnings.append(
                f"{city} is using bundled sample data because live API access failed: {error_message}"
            )
        records.append(record)
    return records, warnings


def persist_alerts(records: list[dict]) -> list[str]:
    """Write alert logs and send optional emails for red alerts."""

    outcomes: list[str] = []
    for record in records:
        if record["triggered"]:
            log_alert(
                city=record["city"],
                rainfall_mm_per_hour=record["rainfall_mm_h"],
                level=record["alert_level"],
                log_path=config.alert_log_path,
            )
            sent, message = send_email_alert(
                city=record["city"],
                rainfall_mm_per_hour=record["rainfall_mm_h"],
                settings=config.email,
            )
            outcomes.append(f"{record['city']}: {message}")
            if sent:
                outcomes.append(f"{record['city']}: email notification sent.")
    return outcomes


def main() -> None:
    """Render the Streamlit application."""

    st_autorefresh(interval=config.refresh_minutes * 60 * 1000, key="rain-refresh")
    st.sidebar.header("Configuration")
    selected_cities = st.sidebar.multiselect(
        "Cities to monitor",
        options=config.cities,
        default=config.cities[:2],
    )
    if not selected_cities:
        st.warning("Please select at least one city to monitor.")
        st.stop()

    if "history" not in st.session_state:
        st.session_state.history = initialize_history(config.cities)

    records, warnings = load_city_data(selected_cities)
    st.title(f"Rainfall Monitor - {records[0]['city']}")
    st.caption(
        "Short-term rainfall monitoring with API integration, threshold alerts, trend prediction, and map visualization."
    )
    for record in records:
        st.session_state.history = append_history(
            st.session_state.history, record["city"], record["rainfall_mm_h"]
        )

    history_df: pd.DataFrame = st.session_state.history
    alert_messages = persist_alerts(records)

    for warning in warnings:
        st.info(warning)
    for message in alert_messages:
        st.warning(message)

    first_city = records[0]
    st.subheader(f"Current focus city: {first_city['city']}")
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Current Rainfall", f"{first_city['rainfall_mm_h']:.2f} mm/h")
    metric_col2.metric("Temperature", f"{first_city['temperature_c']:.1f} °C")
    metric_col3.metric("Humidity", f"{first_city['humidity_pct']}%")

    st.markdown("### Alert Status")
    status_columns = st.columns(len(records))
    for column, record in zip(status_columns, records):
        with column:
            render_alert_card(record)

    summary_rows = []
    for record in records:
        predicted = predict_next_hour(history_df, record["city"])
        summary_rows.append(
            {
                "City": record["city"],
                "Rainfall (mm/h)": round(record["rainfall_mm_h"], 2),
                "Predicted Next Hour (mm/h)": predicted,
                "Alert": record["alert_level"],
                "Weather": record["weather"],
                "Data Source": record["source"],
            }
        )

    st.markdown("### Multi-city Summary")
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    st.markdown("### Historical Trend")
    chart_df = history_df[history_df["city"].isin(selected_cities)].copy()
    st.line_chart(chart_df, x="timestamp", y="rainfall_mm_h", color="city")

    history_plot_path = RESULTS_DIR / "historical_rainfall.png"
    save_history_chart(chart_df, history_plot_path)
    st.caption(f"Saved chart: {history_plot_path}")

    st.markdown("### Optional Extension: Simple 1-hour Prediction")
    prediction_cards = st.columns(len(records))
    for column, record in zip(prediction_cards, records):
        with column:
            st.metric(
                label=f"{record['city']} forecast",
                value=f"{predict_next_hour(history_df, record['city']):.2f} mm/h",
            )

    st.markdown("### Optional Extension: Rainfall Map")
    rainfall_map_path = RESULTS_DIR / "rainfall_map.html"
    rainfall_map = build_rainfall_map(records, rainfall_map_path)
    st_folium(rainfall_map, width=None, height=450)
    st.caption(f"Saved map: {rainfall_map_path}")

    red_alerts = [record for record in records if record["triggered"]]
    st.markdown("### Validation Notes")
    if red_alerts:
        st.error(
            "Heavy rainfall alert triggered for "
            + ", ".join(record["city"] for record in red_alerts)
            + ". Please inspect drainage readiness."
        )
    else:
        st.success("No red alerts at the moment. Current values remain physically reasonable.")

    st.write(
        pd.DataFrame(records)[
            [
                "city",
                "rainfall_mm_h",
                "temperature_c",
                "humidity_pct",
                "weather",
                "alert_level",
                "fetched_at",
            ]
        ]
    )


if __name__ == "__main__":
    main()
