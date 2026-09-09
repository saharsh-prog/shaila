"""
app/views/risk_map.py
─────────────────────
The operational dashboard: a full-bleed dark risk map, a live statistics
panel beside it, and an alert log beneath it.

Layout follows the control-room reference — map dominant, numbers docked to
the right, the log of what is currently firing along the bottom. The reading
order is deliberate: see the district, then the totals, then the specific
cells you would actually call someone about.

This page only reads from app/risk_engine.py. It does not touch the model or
the data pipeline.
"""

from datetime import date

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from app import risk_engine as rk
from app import theme
from app.theme import C

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — controls
# ══════════════════════════════════════════════════════════════════════════════

_min_date, _max_date = rk.available_date_range()
_max_date = max(_max_date, date(2026, 8, 31))

TARGET_DEFAULT_DATE = rk.DEFAULT_DATE
if (
    "shaila_risk_map_date" not in st.session_state
    or st.session_state.shaila_risk_map_date in [date(2025, 5, 30), date(2026, 6, 28), date(2026, 8, 28)]
):
    st.session_state.shaila_risk_map_date = TARGET_DEFAULT_DATE

if st.session_state.get("onpage_risk_date") in [date(2025, 5, 30), date(2026, 6, 28), date(2026, 8, 28)]:
    st.session_state["onpage_risk_date"] = TARGET_DEFAULT_DATE

current_forecast_date = st.session_state.get("onpage_risk_date", st.session_state.shaila_risk_map_date)

with st.sidebar:
    st.markdown(
        f'<div class="sh-kicker" style="margin-bottom:0.7rem">Forecast controls</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="sh-note">Selected Date: <b style="color:{C["text"]}">'
        f'{current_forecast_date.strftime("%d %B %Y")}</b></p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sh-divider"></div>', unsafe_allow_html=True)

    threshold = st.slider(
        "Warning threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.50,
        step=0.05,
        help="Cells at or above this risk are outlined and listed in the alert log.",
    )

    show_incidents = st.toggle(
        "Show verified incidents",
        value=True,
        help="Overlay the 8 documented historical flash flood incidents "
             "as blue rings. These are ground truth, not model output.",
    )

    with st.expander("How to read this map"):
        st.markdown(
            f"""
**Risk = trigger probability × susceptibility multiplier.**

- **Trigger probability** is model output — a RandomForest over soil moisture
  (0–7 cm and 7–28 cm), temperature, and the 3-day / 7-day Antecedent
  Precipitation Index. This is what changes with the date.
- **Susceptibility** is fixed terrain, derived from 1 km mean slope and then
  *floored* to at least "High" wherever ASDMA lists an officially vulnerable
  location or a verified incident occurred. Not model output.
- The multipliers (0.20 / 0.45 / 0.70 / 0.90) are **team-assigned** and
  calibrated to this district's slope distribution — they are not taken from
  a published study.
- **Grey cells are not safe cells.** 93 of the 904 cells lack DEM coverage, so
  their susceptibility is undefined rather than low.
- Colour is backed up by **fill opacity** — darker, more solid cells are higher
  risk — so severity survives red-green colour blindness.
"""
        )

# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# HEADER & NAVIGATION (NAVBAR AT TOP)
# ══════════════════════════════════════════════════════════════════════════════

theme.page_heading(
    f"District risk surface — {current_forecast_date.strftime('%d %B %Y')}",
    f"{theme.APP_SUBTITLE} · 904 cells at 1 km resolution",
)

# ══════════════════════════════════════════════════════════════════════════════
# ON-PAGE FORECAST CONTROLS (BELOW NAVBAR)
# ══════════════════════════════════════════════════════════════════════════════

with st.container():
    c_date, c_space = st.columns([1.5, 3.5], gap="medium")
    with c_date:
        forecast_date = st.date_input(
            "Select Forecast Date",
            value=current_forecast_date,
            min_value=_min_date,
            max_value=_max_date,
            format="DD/MM/YYYY",
            key="onpage_risk_date",
        )
        st.session_state.shaila_risk_map_date = forecast_date

# ══════════════════════════════════════════════════════════════════════════════
# DATA FOR THE SELECTED DATE
# ══════════════════════════════════════════════════════════════════════════════

gdf = rk.build_display_gdf(forecast_date)

has_risk = gdf["risk_probability"].notna()
over = gdf[has_risk & (gdf["risk_probability"] >= threshold)]
counts = rk.severity_counts(gdf)

total_cells = len(gdf)
n_over = len(over)
n_nodata = counts.get("No Data", 0)
peak = gdf["risk_pct"].max()

# ══════════════════════════════════════════════════════════════════════════════
# MAP + STATS PANEL
# ══════════════════════════════════════════════════════════════════════════════

map_col, panel_col = st.columns([2.55, 1], gap="medium")

with map_col:
    fmap = rk.build_folium_map(gdf, threshold, show_incidents=show_incidents)
    # returned_objects=[] stops the map from round-tripping click state on every
    # interaction — the whole page would rerun on a pan otherwise.
    st_folium(
        fmap,
        use_container_width=True,
        height=660,
        returned_objects=[],
    )

with panel_col:
    # ── totals ────────────────────────────────────────────────────────────
    st.markdown(
        theme.panel(
            "Monitoring status",
            theme.stat_row([
                theme.stat(f"{total_cells:,}", "cells"),
                theme.stat(f"{n_over:,}", "above threshold", accent=True),
                theme.stat(
                    "—" if pd.isna(peak) else f"{peak:.0f}%",
                    "peak risk",
                ),
            ])
            + theme.divider()
            + f'<p class="sh-note" style="margin:0">Threshold set to '
              f'<b style="color:{C["text"]}">{threshold:.0%}</b>. '
              f'{n_nodata} cells have no DEM coverage and are excluded from '
              f'the count rather than treated as low risk.</p>',
            count=forecast_date.strftime("%d %b %Y"),
        ),
        unsafe_allow_html=True,
    )

    # ── severity distribution ─────────────────────────────────────────────
    st.markdown(
        theme.panel(
            "Cells per severity band",
            theme.severity_bars(counts, total_cells),
            count=f"{total_cells:,} total",
        ),
        unsafe_allow_html=True,
    )

    # ── legend ────────────────────────────────────────────────────────────
    st.markdown(
        theme.panel("Risk bands", theme.legend()),
        unsafe_allow_html=True,
    )

    # ── model provenance ──────────────────────────────────────────────────
    st.markdown(
        theme.panel(
            "Layer provenance",
            f"""
<p class="sh-note" style="margin:0">
<b style="color:{C['text']}">Trigger</b> · RandomForest, 100 trees,
class-balanced, seed 42 · precomputed cache<br>
<b style="color:{C['text']}">Susceptibility</b> · 1 km mean slope, floored by
the ASDMA official hazard list<br>
<b style="color:{C['text']}">Basemap</b> · Esri Dark Gray
</p>
            """,
        ),
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# EARLY WARNING TABLE (WITH SR NO. AND REVEAL ALL COLUMNS DROPDOWN)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div style="height:0.8rem"></div>', unsafe_allow_html=True)

issued = forecast_date.strftime("%Y-%m-%d")

# Prepare dataframe arranged from most severe cell to least
table_source = over if len(over) > 0 else gdf[gdf["risk_probability"].notna()]
sorted_cells = table_source.sort_values(
    ["risk_probability", "risk_pct"], ascending=[False, False]
).reset_index(drop=True)

sr_nos = list(range(1, len(sorted_cells) + 1))
full_data = pd.DataFrame({
    "Sr No.": sr_nos,
    "Grid ID": sorted_cells["grid_id"],
    "Severity": sorted_cells["severity"],
    "Risk %": sorted_cells["risk_pct"].round(1),
    "Susceptibility": sorted_cells["gsi_susceptibility_class"],
    "Lat": sorted_cells["centroid_lat"].round(4),
    "Lon": sorted_cells["centroid_lon"].round(4),
    "Weather Point ID": sorted_cells["weather_point_id"],
    "Susceptibility Mult": sorted_cells["susceptibility_mult"].round(2),
    "Hazard Floor Applied": sorted_cells["hazard_floor_applied"],
    "Proxy Cell": sorted_cells["is_proxy"],
    "No DEM Coverage": sorted_cells["no_dem"],
    "Risk Probability": sorted_cells["risk_probability"].round(4),
})

standard_cols = ["Sr No.", "Grid ID", "Severity", "Risk %", "Susceptibility", "Lat", "Lon"]
all_cols = list(full_data.columns)

col_title, col_view = st.columns([2.7, 1.3], gap="medium")
with col_title:
    st.markdown(
        f'<div class="sh-panel-title" style="margin-top:0.4rem">'
        f'<span>Early warning alert log</span>'
        f'<span class="sh-count">{len(full_data):,} cells ({len(over)} above threshold)</span></div>',
        unsafe_allow_html=True,
    )
with col_view:
    column_option = st.selectbox(
        "Columns view",
        options=["Standard Columns", "Reveal All Columns", "Custom Selection..."],
        index=0,
        help="Select 'Reveal All Columns' to reveal every column and attribute.",
        label_visibility="collapsed",
    )

if column_option == "Reveal All Columns":
    display_cols = all_cols
elif column_option == "Custom Selection...":
    display_cols = st.multiselect(
        "Select columns to display",
        options=all_cols,
        default=all_cols,
    )
    if not display_cols:
        display_cols = standard_cols
else:
    display_cols = standard_cols

display_df = full_data[display_cols]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)
st.download_button(
    "Download as CSV",
    data=display_df.to_csv(index=False).encode("utf-8"),
    file_name=f"shaila_warnings_{issued}.csv",
    mime="text/csv",
)

st.markdown(theme.render_footer(), unsafe_allow_html=True)
