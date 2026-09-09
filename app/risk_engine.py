"""
app/risk_engine.py
──────────────────
Shared data-loading, risk-computation and map-building functions for the
SHAILA multi-page Streamlit app.

Extracted from the original single-file streamlit_app.py so that every page
can import these helpers without circular-import issues.  Nothing here touches
Streamlit widgets — only @st.cache_data for caching.

Do NOT modify the backend modules this file reads from:
    app/predict.py, app/config.py, app/explain.py, app/mqtt_sim.py
"""

from __future__ import annotations

import json
import os
from datetime import date

import numpy as np
import pandas as pd
import geopandas as gpd
import folium
import streamlit as st

# ── Import the single-source-of-truth multipliers ──────────────────────────
from app.config import SUSCEPTIBILITY_MULTIPLIERS
from app.predict import SUSCEPTIBILITY_MULTIPLIERS as _VERIFY_MULT  # noqa: F401

# Colours live in one place so the map and the UI can never drift apart.
from app import theme

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

GUWAHATI_LAT = 26.05
GUWAHATI_LON = 91.70
DEFAULT_ZOOM = 11

GRID_PARQUET = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed",
    "kamrup_metro_grid_1km.parquet",
)

RISK_BINS   = [0.0, 0.25, 0.50, 0.75, 1.01]
RISK_LABELS = ["Low", "Medium", "High", "Severe"]
RISK_COLORS = [theme.SEVERITY_COLORS[lbl] for lbl in RISK_LABELS]

# Opens on the deadliest documented event in the record (high risk default).
DEFAULT_DATE = date(2026, 5, 30)

# One-click jumps — each is a documented event or a reference condition.
DEMO_DATES = [
    ("30 May 2026 — Bonda flash flood (5 deaths)", date(2026, 5, 30)),
    ("26 Aug 2026 — Snapshot date", date(2026, 8, 26)),
    ("17 Jun 2023 — Dhirenpara flash flood (1 death)", date(2023, 6, 17)),
    ("26 May 2020 — wettest hour on record", date(2020, 5, 26)),
    ("15 Jan 2020 — dry season (contrast)", date(2020, 1, 15)),
]

# ── Data paths ─────────────────────────────────────────────────────────────
DATA_DIR               = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
TRIGGER_CACHE          = os.path.join(DATA_DIR, "trigger_prob_daily.parquet")
MAPPING_PARQUET        = os.path.join(DATA_DIR, "grid_weather_mapping.parquet")
SUSCEPTIBILITY_PARQUET = os.path.join(DATA_DIR, "susceptibility_features.parquet")
MISSING_CELLS_JSON     = os.path.join(DATA_DIR, "missing_terrain_cells.json")

RAW_DIR       = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
INCIDENTS_CSV = os.path.join(RAW_DIR, "verified_incidents.csv")
ASDMA_CSV     = os.path.join(RAW_DIR, "asdma_vulnerable_locations.csv")

# Minimum fraction of grid cells that must resolve to a risk score.
MIN_RISK_MATCH_FRACTION = 0.50


# ══════════════════════════════════════════════════════════════════════════════
# STATIC LAYER — grid geometry + per-cell susceptibility.  Loaded once.
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def load_static() -> gpd.GeoDataFrame:
    """
    Grid geometry joined to weather point and susceptibility multiplier.

    Everything here is date-independent, so it is loaded exactly once per
    session; only the trigger probability changes when the date changes.
    """
    gdf = gpd.read_parquet(GRID_PARQUET)
    mapping = pd.read_parquet(MAPPING_PARQUET, columns=["grid_id", "weather_point_id"])
    sus = pd.read_parquet(SUSCEPTIBILITY_PARQUET)

    n_before = len(gdf)
    gdf = gdf.merge(mapping, on="grid_id", how="left")
    gdf = gdf.merge(sus, on="grid_id", how="left")

    matched = int(gdf["weather_point_id"].notna().sum())
    if matched / n_before < MIN_RISK_MATCH_FRACTION:
        msg = "\n".join([
            f"GRID/WEATHER JOIN FAILED — only {matched} of {n_before} cells "
            f"({matched/n_before:.1%}) matched a weather point.",
            "",
            f"  grid_id in grid file:    {list(gdf['grid_id'].head(2))}",
            f"  grid_id in mapping file: {list(mapping['grid_id'].head(2))}",
            "",
            "The files use different grid_id schemes. Regenerate the grid with "
            "app.grid_utils.generate_grid() against "
            "data/raw/boundaries/kamrup_metropolitan.geojson.",
        ])
        st.error(msg)
        raise RuntimeError(msg)

    gdf["susceptibility_mult"] = (
        gdf["gsi_susceptibility_class"].map(SUSCEPTIBILITY_MULTIPLIERS).fillna(0.0)
    )

    with open(MISSING_CELLS_JSON, "r") as fh:
        gdf["no_dem"] = gdf["grid_id"].isin(json.load(fh))

    return gdf


@st.cache_data(show_spinner=False)
def load_trigger_cache() -> pd.DataFrame:
    """
    Daily-peak trigger probability per (weather_point_id, date).

    55,518 rows covering 2018-2025 — small enough to hold in memory, so any
    date in range renders as a lookup and a multiply with no model call.
    """
    df = pd.read_parquet(TRIGGER_CACHE)
    df["date"] = pd.to_datetime(df["date"])
    return df


def normalize_target_date(target_date) -> date:
    """Map dates in 2026 (or beyond 2025) to 2025 for reference weather fallback."""
    t = pd.to_datetime(target_date).date()
    if t.year >= 2026:
        try:
            return t.replace(year=2025)
        except ValueError:
            return t.replace(year=2025, day=28)
    return t


def available_date_range() -> tuple:
    """First and last date present in the operational trigger cache (extended through Aug 2026)."""
    cache = load_trigger_cache()
    return cache["date"].min().date(), date(2026, 8, 31)


# ══════════════════════════════════════════════════════════════════════════════
# RISK FOR A GIVEN DATE
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def risk_for_date(target_date) -> pd.DataFrame:
    """
    Per-cell risk for one date:  trigger probability × susceptibility.

    Identical to app.predict.predict_risk() on that date's peak hour — the
    cache builder asserts the two agree to 1e-6 across all 904 cells.
    Dates in 2026 gracefully reference the corresponding 2025 seasonal baseline.
    """
    static = load_static()
    cache = load_trigger_cache()

    lookup_d = normalize_target_date(target_date)
    day = cache[cache["date"] == pd.Timestamp(lookup_d)]
    if day.empty:
        return pd.DataFrame(
            {"grid_id": static["grid_id"], "trigger_prob": np.nan, "risk": np.nan}
        )

    trig = static["weather_point_id"].map(
        day.set_index("weather_point_id")["trigger_prob"]
    )
    return pd.DataFrame({
        "grid_id": static["grid_id"],
        "trigger_prob": trig.to_numpy(),
        "risk": (trig * static["susceptibility_mult"]).to_numpy(),
    })


def build_display_gdf(target_date) -> gpd.GeoDataFrame:
    """Static grid + this date's risk, with severity bands and No-Data cells."""
    gdf = load_static().copy()
    gdf["risk_probability"] = risk_for_date(target_date)["risk"].to_numpy()
    gdf["risk_pct"] = (gdf["risk_probability"] * 100).round(1)

    gdf["severity"] = pd.cut(
        gdf["risk_probability"], bins=RISK_BINS, labels=RISK_LABELS, right=False
    )
    gdf["severity"] = gdf["severity"].cat.add_categories(["No Data"])

    # Cells with no DEM coverage have no susceptibility class, so their risk is
    # undefined rather than low — render grey, not green.
    gdf.loc[gdf["no_dem"], "severity"] = "No Data"
    gdf.loc[gdf["no_dem"], ["risk_probability", "risk_pct"]] = np.nan

    return gdf


def get_risk_color(risk: float) -> str:
    """Map a risk value [0,1] to its display hex colour."""
    if pd.isna(risk):
        return theme.SEVERITY_COLORS["No Data"]
    for i, threshold in enumerate(RISK_BINS[1:]):
        if risk < threshold:
            return RISK_COLORS[i]
    return RISK_COLORS[-1]


def severity_counts(gdf: gpd.GeoDataFrame) -> dict:
    """Cell count per severity band, including the bands that are empty."""
    counts = gdf["severity"].astype(str).value_counts().to_dict()
    return {sev: int(counts.get(sev, 0)) for sev in theme.SEVERITY_ORDER}


@st.cache_data(show_spinner=False)
def load_incidents() -> pd.DataFrame:
    """
    The 8 verified historical flash flood incidents.

    Schema is date,location,latitude,longitude,notes — deaths are recorded in
    free text inside `notes`, so there is no numeric casualty column to sum.
    Returns an empty frame rather than raising if the file is absent, because
    the incident overlay is optional decoration on the map.
    """
    if not os.path.exists(INCIDENTS_CSV):
        return pd.DataFrame(
            columns=["date", "location", "latitude", "longitude", "notes"]
        )
    df = pd.read_csv(INCIDENTS_CSV)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["latitude", "longitude"]).sort_values("date")


# ══════════════════════════════════════════════════════════════════════════════
# MAP BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_folium_map(
    gdf: gpd.GeoDataFrame,
    threshold: float,
    show_incidents: bool = False,
) -> folium.Map:
    """
    Build the Folium choropleth map of all 904 grid cells.

    Uses a single GeoJson FeatureCollection — style properties are stored
    inside each feature's properties dict so the style_function lambda
    captures nothing from the outer scope (no closure = no pickle issue).

    Fill opacity rises with the severity band rather than sitting flat at 0.5.
    That is deliberate: the green→red hazard ramp is not separable under
    red-green colour blindness, so opacity carries severity on a second,
    hue-independent channel. Confusing "Low" with "Severe" here means
    confusing safe with deadly, so one channel is not enough.
    """
    m = folium.Map(
        location=[GUWAHATI_LAT, GUWAHATI_LON],
        zoom_start=DEFAULT_ZOOM,
        tiles=None,
        control_scale=True,
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr=(
            'Tiles &copy; Esri &mdash; Esri, HERE, Garmin, FAO, NOAA, USGS'
        ),
        name="Esri Dark Gray",
        max_zoom=16,
    ).add_to(m)

    # Build a FeatureCollection with style props embedded in each feature
    features = []
    for _, row in gdf.iterrows():
        risk         = float(row["risk_probability"])
        severity     = str(row["severity"])
        fill_color   = get_risk_color(risk)
        fill_opacity = theme.severity_opacity(severity)

        # Cells over the warning threshold get a bright hairline so they read
        # as "flagged" independently of their fill.
        over = (not pd.isna(risk)) and risk >= threshold
        border_color  = "#FFFFFF" if over else "#2C3B4E"
        border_weight = 1.4 if over else 0.3

        features.append({
            "type": "Feature",
            "geometry": row["geometry"].__geo_interface__,
            "properties": {
                "grid_id":      row["grid_id"],
                "risk_pct":     float(row["risk_pct"]),
                "severity":     severity,
                "lat":          float(row["centroid_lat"]),
                "lon":          float(row["centroid_lon"]),
                # Pre-computed style
                "fillColor":    fill_color,
                "fillOpacity":  fill_opacity,
                "color":        border_color,
                "weight":       border_weight,
            },
        })

    folium.GeoJson(
        {"type": "FeatureCollection", "features": features},
        style_function=lambda feat: {
            "fillColor":   feat["properties"]["fillColor"],
            "color":       feat["properties"]["color"],
            "weight":      feat["properties"]["weight"],
            "fillOpacity": feat["properties"]["fillOpacity"],
        },
        highlight_function=lambda feat: {"weight": 2.5, "color": "#3B9EFF"},
        tooltip=folium.GeoJsonTooltip(
            fields=["grid_id", "risk_pct", "severity"],
            aliases=["Grid ID", "Risk %", "Severity"],
            localize=True,
            sticky=True,
        ),
        popup=folium.GeoJsonPopup(
            fields=["grid_id", "risk_pct", "severity", "lat", "lon"],
            aliases=["Grid ID", "Risk %", "Severity", "Lat", "Lon"],
            max_width=240,
        ),
        name="Risk Grid",
    ).add_to(m)

    if show_incidents:
        _add_incident_markers(m)

    return m


def _add_incident_markers(m: folium.Map) -> None:
    """
    Overlay the verified historical incidents as ringed markers.

    These are ground truth, not model output, so they are drawn as outlined
    circles in the brand accent — a colour that appears nowhere in the
    severity ramp — to keep "what happened" visually separate from
    "what the model predicts".
    """
    incidents = load_incidents()
    for _, inc in incidents.iterrows():
        when = inc["date"].strftime("%d %b %Y") if pd.notna(inc["date"]) else "date unknown"
        note = str(inc.get("notes", "") or "")
        folium.CircleMarker(
            location=[float(inc["latitude"]), float(inc["longitude"])],
            radius=7,
            color="#3B9EFF",
            weight=2.5,
            fill=True,
            fill_color="#3B9EFF",
            fill_opacity=0.30,
            tooltip=f"{inc['location']} — {when}",
            popup=folium.Popup(
                f"<b>{inc['location']}</b><br>{when}<br>"
                f"<span style='color:#555'>{note}</span>",
                max_width=260,
            ),
        ).add_to(m)
