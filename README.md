# SHAILA (शैल) — Flash-Flood Early Warning System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.62.0-red.svg)](https://streamlit.io/)
[![GeoPandas](https://img.shields.io/badge/GeoPandas-1.1.4-green.svg)](https://geopandas.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

**SHAILA (शैल)** is a high-resolution, spatial-hydrological risk assessment and early warning dashboard. It monitors flash-flood and rainfall-triggered landslide hazards across a **1 km² resolution grid**.

---

## 📌 Key Features

- **Dual-Factor Risk Formulation**: Combines static geophysical susceptibility with dynamic hydrometeorological trigger modeling:
  $$\text{Composite Risk} = \text{Trigger Probability} \times \text{Susceptibility Multiplier}$$
- **1 km² Spatial Discretization**: uniform grid cells covering the entire district with digital elevation, slope analysis, and ASDMA vulnerable point intersections.
- **Machine Learning Dynamic Trigger Model**: Trained `RandomForestClassifier` utilizing leak-safe antecedent precipitation indices (API 3-day and 7-day), root-zone and surface soil moisture levels, and temperature.
- **Interactive Multi-Page GIS Dashboard**: Built on Streamlit and Folium choropleths with layer controls, date pickers, district statistics, and per-cell risk explainers.
- **Simulated IoT Sensor Telemetry Feed**: Real-time MQTT stream ingestion demo displaying node-level water levels and soil saturation for critical drainage junctions.

---

## 🏛️ System Architecture

```
                                  ┌────────────────────────┐
                                  │   Open-Meteo ERA5-Land  │
                                  │  (19 Weather Points)   │
                                  └───────────┬────────────┘
                                              │
┌────────────────────────┐                    ▼
│  DEM & Topography /    │       ┌────────────────────────┐
│ ASDMA Hazard Locations │       │  RandomForest Classifier│
└───────────┬────────────┘       │ (Hydrometeorological)  │
            │                    └───────────┬────────────┘
            ▼                                │
 ┌──────────────────────┐                    ▼
 │ Static Susceptibility│         ┌──────────────────────┐
 │ (Low / Mod / High /  │         │ Dynamic Trigger Prob │
 │      Very High)      │         │   (0.00 to 1.00)     │
 └──────────┬───────────┘         └──────────┬───────────┘
            │                                │
            └───────────────┬────────────────┘
                            ▼
              ┌───────────────────────────┐
              │    Composite Cell Risk    │
              │  Risk = Trigger × Suscep  │
              └─────────────┬─────────────┘
                            ▼
              ┌───────────────────────────┐
              │ Streamlit Map & Analytics │
              │  (views/risk_map, views/  │
              │   home, views/insights)   │
              └───────────────────────────┘
```

---

## 🚀 Getting Started: Running Locally

### 1. Prerequisites
- **Python**: Version `3.10` or higher (`3.10` – `3.14` supported).
- **Git** (optional, for version control).

### 2. Clone or Navigate to the Repository
```bash
cd /path/to/shaila
```
*(Ensure all commands are executed from the **repository root** so relative paths to `data/` and `models/` resolve properly).*

### 3. Create & Activate a Virtual Environment
- **On Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **On Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note**: Core dependencies include `streamlit`, `pandas`, `numpy`, `geopandas`, `shapely`, `scikit-learn`, `folium`, `streamlit-folium`, `pyarrow`, and `paho-mqtt`.

### 5. Launch the Streamlit App
Run the multipage Streamlit entrypoint from the repository root:
```bash
streamlit run app/streamlit_app.py
```
Or alternatively with Python module syntax:
```bash
python -m streamlit run app/streamlit_app.py
```

### 6. Access the Application
Open your web browser and navigate to:
```
http://localhost:8501
```

#### Useful CLI Flags:
- Run on a specific port:
  ```bash
  streamlit run app/streamlit_app.py --server.port 8080
  ```
- Run headlessly without auto-opening a browser:
  ```bash
  streamlit run app/streamlit_app.py --server.headless true
  ```

---

## 📂 Project Structure

```plaintext
shaila/
├── app/
│   ├── assets/                 # Brand assets and styling icons
│   ├── views/                  # Streamlit multipage views
│   │   ├── home.py             # District hazard summary and overview
│   │   ├── risk_map.py         # 1 km interactive choropleth map & cell inspector
│   │   ├── insights.py         # Historical event analysis & feature insights
│   │   └── about.py            # Methodology, data sources, and disclosures
│   ├── config.py               # Shared constants and susceptibility multipliers
│   ├── explain.py              # Per-cell risk factor breakdown and explainers
│   ├── features.py             # Feature assembly pipeline
│   ├── grid_utils.py           # 1 km grid generation and spatial indexing
│   ├── labelling.py            # Event labeling & threshold definitions
│   ├── mqtt_sim.py             # IoT sensor telemetry simulation client
│   ├── predict.py              # Inference pipeline for cell-level risk
│   ├── risk_engine.py          # Spatial risk aggregation and scoring engine
│   ├── streamlit_app.py        # Application entrypoint & navigation router
│   ├── susceptibility_utils.py # Slope classification & ASDMA hazard flooring
│   ├── terrain_utils.py        # DEM & slope calculation utilities
│   ├── theme.py                # CSS theming and typography injection
│   ├── train_trigger_model.py  # Model training pipeline (RandomForest & XGBoost)
│   └── weather_fetch.py        # Weather data fetching and feature engineering
├── build_susceptibility.py     # Script to regenerate static susceptibility layer
├── build_trigger_cache.py      # Script to precompute daily trigger probabilities
├── data/
│   ├── raw/
│   │   ├── asdma_vulnerable_locations.csv  # Official ASDMA vulnerable sites
│   │   └── verified_incidents.csv          # Historic ground-truth events
│   └── processed/
│       ├── kamrup_metro_grid_1km.parquet   # 904 1-km grid polygons
│       ├── terrain_features.parquet        # Mean slope & elevation per cell
│       ├── susceptibility_features.parquet # Static susceptibility classes
│       ├── grid_weather_mapping.parquet    # Cell-to-weather station mapping
│       ├── weather_hourly.parquet          # Reanalysis meteorological records
│       └── trigger_prob_daily.parquet      # Precalculated trigger probabilities
├── docs/
│   ├── PROJECT_STATUS.md       # Technical audit and pipeline findings
│   └── model_training_log.md   # Rigorous evaluation log & split methodologies
├── models/
│   └── random_forest_trigger_model.pkl # Trained trigger model artifact
├── notebooks/                  # Exploratory & pipeline development notebooks
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## ⚙️ Data Pipeline & Offline Maintenance

All preprocessed data files and trained model artifacts are included in the repository. If you update raw inputs or tweak model hyperparameters, rerun the pipeline using these scripts:

1. **Regenerate Susceptibility Features**:
   Calculates terrain slopes from DEM and enforces ASDMA vulnerable hazard minimums:
   ```bash
   python build_susceptibility.py
   ```

2. **Recompute Daily Trigger Probability Cache**:
   Evaluates the Random Forest model :
   ```bash
   python build_trigger_cache.py
   ```

3. **Retrain the Dynamic Trigger Model**:
   Trains candidate models (RandomForest and XGBoost) using leak-free episode grouping:
   ```bash
   python -m app.train_trigger_model
   ```

---

## 📊 Application Pages Overview

| Page | Path | Description |
|---|---|---|
| **Home** | `/` | Executive summary, current district-level warning level, key risk drivers, and IoT sensor quick-status. |
| **Risk Map** | `/risk_map` | Full interactive GIS map with 1 km grid polygons, severity coloring (Low to Severe), date selector (2018–2025), and detailed cell inspection on click. |
| **Insights** | `/insights` | In-depth retrospective analysis of severe flood episodes (e.g. Cyclone Remal 2024, June 2022 Floods) and model feature importance curves. |
| **Method & Data** | `/about` | Documentation of mathematical models, data sources, scientific limitations, and audit disclosures. |

---
 
 Designed and developed by CODE CLAN.
 THINK-CODE-CONQUER