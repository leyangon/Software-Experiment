Software Development
实验报告
使用 OpenAI Codex
辅助完成短时降雨监测与预警系统

姓名
刘子康
班级
S4280
学号
3124358273
Email
leyangon@qq.com
日期
2026-04-21

## Abstract

This experiment implemented a short-term rainfall monitoring and alert system based on the guide `Experiment1_Rainfall_Alert`. The project integrates the OpenWeatherMap API, extracts rainfall intensity from live weather responses, applies threshold-based alert logic, and presents the results through a Streamlit dashboard. To make the system robust and easy to demonstrate, a bundled offline sample dataset was added so that the application remains runnable even when an API key is unavailable or network access fails. The system fulfills all core requirements of the experiment, including API integration, alert classification, timestamped alert logging, dashboard construction, and documentation of AI-assisted development through a prompt log. In addition, all optional extensions were implemented: multi-city monitoring, configurable email notification, simple rainfall prediction based on recent historical trends, and map visualization using Folium. Verification results show that the threshold logic behaves correctly at 10 mm/h and 20 mm/h, alert events are written to the log with timestamps, and the generated rainfall values remain physically reasonable for short-term urban rainfall monitoring. The experiment demonstrates that AI-assisted programming can accelerate development while still requiring the student to inspect API details, refine error handling, and validate the final system against domain knowledge.

## 1 Experimental Objectives

The objective of this experiment was to build a complete short-term rainfall forecasting and alert system for urban flood management scenarios, while practicing AI-assisted software development in a controlled laboratory task.

The specific goals were as follows:

- To integrate an external weather API and extract rainfall-related information from real responses.
- To implement threshold-based rainfall alert logic according to the experiment requirements.
- To construct a real-time visual dashboard using Streamlit.
- To log alert events in a clear and verifiable format.
- To validate whether the generated rainfall values and alert judgments are physically reasonable.
- To document the interaction process with AI tools and record corrections made during development.
- To extend the basic system with additional engineering functions when time allowed.

## 2 Experimental Process

### 2.1 Task Description

According to the experiment guide, the system needed to complete four major tasks: weather API integration, alert logic implementation, dashboard creation, and testing with validation. The final deliverables included the main application file, an alert log, a prompt log, and a screenshot of the dashboard. The optional extensions suggested in the guide were also completed in this project.

The final project was stored in:

`/Users/leyangon/Desktop/Experiments/Experiment1`

The main program is `weather_monitor.py`, and the supporting logic is placed in the `src/` directory for better modularity.

### 2.2 Environment Setup and Project Structure

The experiment required Python 3.10 or above. A dedicated virtual environment was created in the project directory to isolate dependencies. The key third-party libraries were `requests`, `pandas`, `streamlit`, `folium`, `streamlit-folium`, `matplotlib`, and `pytest`.

The project structure is shown below:

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
│   ├── conftest.py
│   └── test_alerting.py
├── README.md
└── weather_monitor.py
```

This structure keeps the program easy to read and suitable for a student experiment. The top-level script is responsible for the Streamlit interface, while the source directory separates configuration loading, API access, alert processing, and analytics functions.

### 2.3 API Integration

The weather data source used in this experiment was the OpenWeatherMap current weather API. The API client was implemented in `src/weather_api.py`. The code sends a request through the `requests` library and extracts the following key fields from the response:

- city name
- country code
- rainfall intensity in mm/h
- temperature
- humidity
- weather description
- longitude and latitude

One practical difficulty is that OpenWeatherMap does not always return rainfall information in exactly the same form. In some cases, rainfall appears as `rain["1h"]`, while in others it may appear as `rain["3h"]`, and sometimes the field is absent entirely when there is no rain. Therefore, the rainfall extraction logic was refined so that:

- `rain["1h"]` is used directly when available;
- `rain["3h"] / 3` is used as an hourly approximation when only 3-hour rainfall is available;
- `0.0` is returned when no rainfall field exists.

To improve robustness, the system does not fail completely when live API access is unavailable. Instead, it falls back to bundled sample data stored in `data/sample_weather.json`. This design makes the project easy to demonstrate during class and prevents network-related issues from blocking the experiment.

### 2.4 Alert Logic Implementation

The alert logic strictly follows the thresholds given in the experiment guide:

- Green: rainfall < 10 mm/h
- Yellow: 10 <= rainfall < 20 mm/h
- Red: rainfall >= 20 mm/h

The implementation is placed in `src/alerting.py`. Each rainfall value is converted into an `AlertResult` object that contains the alert level, display color, description, and whether the alert is triggered.

When a red alert occurs, the system performs the following actions automatically:

- displays a warning message in the dashboard;
- appends an alert record to `alert_log.txt`;
- attempts to send an email notification if SMTP settings have been configured.

Each log entry uses an ISO-format timestamp so that the alert history can be verified clearly during testing.

### 2.5 Dashboard Design

The visual interface was implemented with Streamlit in `weather_monitor.py`. The dashboard contains the following components:

- page title and experiment description;
- sidebar for city selection;
- current rainfall, temperature, and humidity metrics for the focus city;
- color-coded alert status cards for all selected cities;
- a multi-city summary table;
- a historical rainfall trend chart;
- a one-hour rainfall prediction panel;
- a Folium-based rainfall map;
- validation notes indicating whether red alerts have been triggered.

The dashboard is configured to auto-refresh every five minutes, which satisfies the real-time display requirement from the guide. The generated historical chart is saved to `results/historical_rainfall.png`, and the generated map is saved to `results/rainfall_map.html`.

### 2.6 Optional Extensions

All optional extensions listed in the guide were addressed in this project.

First, multiple city monitoring was implemented through a Streamlit multiselect control. This allows simultaneous comparison of rainfall conditions in Beijing, Shanghai, Guangzhou, and Shenzhen.

Second, email notification support was added as a configurable extension. Because email credentials are environment-specific, the feature is disabled by default and only becomes active when the required SMTP environment variables are provided.

Third, a simple rainfall prediction function was implemented using a linear trend estimated from recent historical observations. Although this is not a professional forecasting model, it is sufficient as an experimental extension to show how historical data can be used to predict near-future rainfall.

Fourth, a rainfall map was created using Folium. Each monitored city is marked on the map, and the marker color matches the current alert status. This extension improves the spatial readability of the dashboard.

### 2.7 Testing and Validation

The project was verified in two ways. First, unit tests were written for the most important deterministic functions. The tests checked:

- correct threshold classification for green, yellow, and red alerts;
- correct rainfall parsing priority for `rain["1h"]`;
- correct log writing behavior.

The test command was:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest
```

The result was:

```text
3 passed in 3.64s
```

Second, the modules were imported directly in the virtual environment to verify that the application structure is valid. Streamlit emitted a normal warning about a missing script context during plain module import, but the import completed successfully, which shows that the code is syntactically valid and properly organized.

From the perspective of physical reasonableness, the rainfall samples used in the project range from light rain to heavy rainfall, which is consistent with short-term urban weather conditions. In particular, the red alert example in Guangzhou was set above 20 mm/h to match the experiment threshold and provide a clear test case for logging and warnings.

## 3 Results and Analysis

### 3.1 Functional Completion

The project completed all mandatory tasks in the experiment guide:

- successful API integration with error handling;
- rainfall intensity extraction;
- threshold-based alert classification;
- alert logging with timestamps;
- a functional Streamlit dashboard;
- testing and validation records;
- prompt log documentation.

In addition, all optional extension tasks were implemented rather than omitted.

### 3.2 Engineering Characteristics

Compared with a minimal one-file student script, the final system has better engineering quality. The logic is divided into modules, configuration is handled through environment variables, and offline fallback data is provided for stable demonstration. This makes the program more reliable in practice and easier to maintain.

Another important improvement is that the application was designed to remain usable under imperfect conditions. In AI-generated first drafts, it is common to assume that the API key is always valid and rainfall fields are always present. During this experiment, these assumptions were corrected deliberately. As a result, the final program is more robust and better aligned with real software development needs.

### 3.3 Role of AI Assistance

AI assistance was useful in rapidly drafting the project skeleton, proposing module boundaries, and generating initial code for API calls and Streamlit layout. However, the final quality depended on human review and correction. Several issues required explicit refinement, including rainfall field parsing, fallback logic for offline demonstration, configurable email alerts, and testing configuration.

This shows that AI-assisted programming is most effective when used as a collaborative development tool rather than as a fully autonomous replacement for reasoning. The student still needs to inspect API behavior, verify edge cases, and ensure that the implementation matches the experimental objectives.

## 4 Summary

This experiment successfully completed the design and implementation of a short-term rainfall monitoring and alert system based on the given guide. The final system integrates weather API access, rainfall intensity extraction, threshold alerting, alert logging, and a real-time Streamlit dashboard. It also includes multi-city monitoring, simple prediction, map visualization, and configurable email notification as optional extensions.

Through the experiment, I gained a clearer understanding of three aspects. First, I learned how to connect a Python program with a real web API and convert raw JSON responses into engineering-ready application data. Second, I learned how threshold rules can be translated into practical alert logic and presented clearly in a dashboard interface. Third, I gained deeper experience with AI-assisted software development. AI can generate useful initial solutions quickly, but robust final results still require careful checking, testing, and domain-based validation.

Overall, this experiment not only fulfilled the assignment requirements, but also showed how AI can support problem decomposition, coding efficiency, and software structuring when combined with responsible human review.
