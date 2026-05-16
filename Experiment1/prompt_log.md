# Prompt Log

## Prompt 1: API Integration

Write Python code to fetch current weather data for a city from OpenWeatherMap using `requests`. The code should extract rainfall intensity, handle API errors gracefully, and be suitable for a Streamlit rainfall monitoring dashboard.

### AI Output Review

- The initial idea of calling the OpenWeatherMap current weather endpoint was correct.
- A correction was needed for rainfall parsing because the API may return `rain["1h"]`, `rain["3h"]`, or no rainfall field at all.
- Error handling was strengthened so the system can fall back to bundled sample data when the live API request fails.

## Prompt 2: Alert Logic

Implement rainfall alert logic using thresholds: Green below 10 mm/h, Yellow for 10 to below 20 mm/h, and Red for 20 mm/h or above. When Red is triggered, log the event with timestamp and optionally send a notification.

### AI Output Review

- The threshold classification was retained.
- Logging was refined to append ISO-format timestamps and key event information to `alert_log.txt`.
- Email notification was implemented as an optional extension with safe default behavior.

## Prompt 3: Dashboard

Build a Streamlit dashboard titled `Rainfall Monitor - [City Name]` that shows current rainfall, color-coded alert status, historical data, and auto-refresh behavior.

### AI Output Review

- The dashboard was extended from a single-city view to multi-city monitoring.
- Historical trend and table components were added for easier validation.
- A Folium map and one-hour trend prediction were included to satisfy optional extensions.

## Prompt 4: Validation

Review the generated system for possible AI mistakes and physical reasonableness.

### AI Output Review

- Potential issue found: some generated implementations assume rainfall data is always present. This was corrected by returning `0.0` when rainfall fields are absent.
- Potential issue found: API-dependent applications may fail completely without credentials or internet access. This was corrected with bundled sample data and explicit warning messages.
- Physical reasonableness was checked by ensuring rainfall intensity values match common short-term rainfall ranges and trigger thresholds consistently.
