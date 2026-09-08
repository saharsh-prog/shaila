"""
app/streamlit_app.py
────────────────────
SHAILA (शैल) — Flash-Flood Early Warning System
Kamrup Metropolitan District, Assam

Run from the REPOSITORY ROOT (every data path below is cwd-relative):
    streamlit run app/streamlit_app.py

This file is the multipage entrypoint and nothing else. It sets the page
config, injects the theme, and hands off to st.navigation. All rendering
lives in app/views/, all data work in app/risk_engine.py.

Why app/views/ and not app/pages/
─────────────────────────────────
A directory literally named `pages/` beside the entrypoint triggers
Streamlit's legacy auto-multipage detection, which would build a second
navigation on top of the one declared here. `views/` avoids that entirely.

What is real and what is simulated
──────────────────────────────────
REAL       Risk scores, for any date from 2018-01-01 to 2025-12-31.
             risk[cell, date] = trigger_prob[weather_point(cell), date]
                                * susceptibility_multiplier[cell]
           Trigger probabilities come from the RandomForest model via the
           precomputed cache (build_trigger_cache.py, 55,518 rows); the
           susceptibility layer is terrain-derived and floored by ASDMA's
           officially identified vulnerable locations
           (build_susceptibility.py). The cache builder asserts this
           matches app/predict.py to 1e-6 on all 904 cells.
SIMULATED  IoT sensor telemetry (app/mqtt_sim.py). No public
           village-level sensor network exists; the panel demonstrates
           the ingestion interface a real feed would drop into. This is
           disclosed in the UI and must stay disclosed.

Regenerating after a model or multiplier change
───────────────────────────────────────────────
    python build_susceptibility.py     # susceptibility classes
    python build_trigger_cache.py      # trigger probability cache

Do NOT import or modify:
    app/grid_utils.py, app/weather_fetch.py, app/terrain_utils.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from app import theme  # noqa: E402

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG — must run before st.navigation
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SHAILA — Flash-Flood Early Warning System",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

theme.inject_theme()

# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

HOME = st.Page(
    "views/home.py",
    title="Home",
    url_path="",
    default=True,
)
RISK_MAP = st.Page(
    "views/risk_map.py",
    title="Risk Map",
    url_path="risk_map",
)
INSIGHTS = st.Page(
    "views/insights.py",
    title="Insights",
    url_path="insights",
)
ABOUT = st.Page(
    "views/about.py",
    title="Method & Data",
    url_path="about",
)

nav = st.navigation([HOME, RISK_MAP, INSIGHTS, ABOUT], position="hidden")
nav.run()
