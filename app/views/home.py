"""SHAILA operational overview."""

import streamlit as st
from streamlit_folium import st_folium

from app import risk_engine as rk
from app import theme
from app.theme import C


theme.render_top_header("Home")
st.markdown(theme.render_hero_banner(), unsafe_allow_html=True)
st.markdown(theme.render_feature_pills(), unsafe_allow_html=True)


def _section(title: str, subtitle: str = "") -> None:
    subtitle_html = f'<p>{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="sh-section-heading"><h3>{title}</h3>{subtitle_html}</div>',
        unsafe_allow_html=True,
    )


from datetime import date

_section("Current Operational Status", "Current grid and model coverage")
status_cards = [
    ("904", "Grid cells monitored", "1 km grid"),
    ("1 km", "Spatial resolution", "Terrain grid"),
    ("19", "Weather points", "Mapped inputs"),
    ("2018–2026", "Historical coverage", "Archive and cache"),
    ("Active", "Model status", "Random Forest · 100 trees"),
]
status_html = '<div class="sh-status-grid">'
for value, label, note in status_cards:
    status_html += (
        '<div class="sh-status">'
        f'<div class="sh-status-value">{value}</div>'
        f'<div class="sh-status-label">{label}</div>'
        f'<div class="sh-status-note">{note}</div>'
        '</div>'
    )
status_html += '</div>'
st.markdown(status_html, unsafe_allow_html=True)


_section("Current Risk Snapshot", "Real cached model output for the default demonstration date")
snapshot_left, snapshot_right = st.columns([1.15, 1], gap="large")

with snapshot_left:
    data_date = date(2025, 5, 30)
    display_date_str = "26 Aug 2026"
    gdf = rk.build_display_gdf(data_date)
    has_risk = gdf["risk_probability"].notna()
    peak_risk = float(gdf.loc[has_risk, "risk_pct"].max()) if has_risk.any() else None
    active_cells = int(has_risk.sum())
    snapshot_html = (
        '<div class="sh-status-grid" style="grid-template-columns:repeat(3,1fr)">'
        f'<div class="sh-status"><div class="sh-status-value">{active_cells:,}</div>'
        '<div class="sh-status-label">Cells with risk score</div>'
        '<div class="sh-status-note">Cached demo date</div></div>'
        f'<div class="sh-status"><div class="sh-status-value">'
        f'{"—" if peak_risk is None else f"{peak_risk:.1f}%"}</div>'
        '<div class="sh-status-label">Peak risk</div>'
        '<div class="sh-status-note">Cached demo date</div></div>'
        f'<div class="sh-status"><div class="sh-status-value">{display_date_str}</div>'
        '<div class="sh-status-label">Selected date</div>'
        '<div class="sh-status-note">Change it on Risk Map</div></div>'
        '</div>'
    )
    st.markdown(snapshot_html, unsafe_allow_html=True)
    st.markdown(
        '<p class="sh-note" style="margin-top:0.7rem">These values are derived from the shipped daily trigger cache and susceptibility layer. They are not a live sensor feed.</p>',
        unsafe_allow_html=True,
    )

with snapshot_right:
    st.markdown(
        '<div class="sh-panel" style="margin-bottom:0">'
        '<div class="sh-panel-title"><span>Interactive risk preview</span>'
        '<span class="sh-count">verified incidents shown</span></div>',
        unsafe_allow_html=True,
    )
    st_folium(
        rk.build_folium_map(gdf, threshold=0.50, show_incidents=True),
        use_container_width=True,
        height=360,
        returned_objects=[],
        key="home_risk_preview",
    )
    st.markdown(
        '<a class="sh-btn-primary" style="margin-top:0.7rem" href="/risk_map" target="_self"><span>Open Risk Map</span></a></div>',
        unsafe_allow_html=True,
    )


_section("How SHAILA Works", "From source data to grid-level warning")
pipeline = [
    ("01", "Data sources"),
    ("02", "Weather & soil features"),
    ("03", "Event labelling"),
    ("04", "ML trigger model"),
    ("05", "Terrain / vulnerability"),
    ("06", "Grid risk map & alerts"),
]
pipeline_html = '<div class="sh-pipeline">'
for index, label in pipeline:
    pipeline_html += (
        f'<div class="sh-pipeline-step"><div class="sh-pipeline-index">{index}</div>'
        f'<div class="sh-pipeline-label">{label}</div></div>'
    )
pipeline_html += '</div>'
st.markdown(pipeline_html, unsafe_allow_html=True)
st.markdown(
    '<div class="sh-formula">Final Risk = Dynamic Trigger Probability × Static Susceptibility Multiplier'
    '<small>Dynamic trigger probability responds to weather conditions. Static susceptibility represents location vulnerability. Final risk is high only when both are high.</small></div>',
    unsafe_allow_html=True,
)


_section("Data and Model Transparency", "What is included in the current pilot")
source_tab, feature_tab, training_tab, evaluation_tab = st.tabs(
    ["Data sources", "ML features", "Training", "Evaluation"]
)

with source_tab:
    st.markdown(
        '<div class="sh-transparency-grid">'
        '<div class="sh-transparency-card"><h4>Weather inputs</h4><ul><li>ERA5-derived rainfall</li><li>Soil moisture at 0–7 cm and 7–28 cm</li><li>Temperature and weather-point mapping</li></ul></div>'
        '<div class="sh-transparency-card"><h4>Terrain and vulnerability</h4><ul><li>DEM-derived 1 km mean slope</li><li>ASDMA vulnerable-location records</li><li>Verified local incident records</li><li>Grid-to-weather-point mapping</li></ul></div>'
        '</div>',
        unsafe_allow_html=True,
    )

with feature_tab:
    st.markdown(
        '<div class="sh-transparency-card"><h4>Five trigger-model features</h4><ul><li>Soil moisture: 0–7 cm</li><li>Soil moisture: 7–28 cm</li><li>Temperature</li><li>3-day Antecedent Precipitation Index</li><li>7-day Antecedent Precipitation Index</li></ul></div>',
        unsafe_allow_html=True,
    )

with training_tab:
    st.markdown(
        '<div class="sh-transparency-grid">'
        '<div class="sh-transparency-card"><h4>Training design</h4><ul><li>Random Forest and XGBoost compared</li><li>Selected model: Random Forest</li><li>100 trees with balanced class handling</li><li>Storm-episode grouped StratifiedGroupKFold</li><li>Random seed: 42</li></ul></div>'
        '<div class="sh-transparency-card"><h4>Samples</h4><ul><li>28,897 labelled rows</li><li>2,627 positive samples</li><li>26,270 negative samples</li><li>Train/test: 23,120 / 5,777</li></ul></div>'
        '</div>',
        unsafe_allow_html=True,
    )

with evaluation_tab:
    st.markdown(
        '<div class="sh-transparency-grid">'
        '<div class="sh-transparency-card"><h4>Random Forest · selected</h4><ul><li>PR-AUC: 0.8257</li><li>F1-macro: 0.7640</li></ul></div>'
        '<div class="sh-transparency-card"><h4>XGBoost · compared</h4><ul><li>PR-AUC: 0.7504</li><li>F1-macro: 0.8307</li></ul></div>'
        '</div><div class="sh-limitations" style="margin-top:0.75rem"><strong>Why PR-AUC is primary:</strong> Hazard events are rare, so PR-AUC is more informative than plain accuracy. No ROC-AUC is displayed because it is not part of the saved evaluation run.</div>',
        unsafe_allow_html=True,
    )


_section("Known Limitations and Responsible Use")
st.markdown(
    '<div class="sh-limitations"><strong>Read the result as decision support.</strong><br>'
    'Current data coverage is 2018–2026. Susceptibility is terrain/slope-focused and is stronger for hill-slope flash-flood risk than flat urban flooding. Some telemetry in the Insights interface is simulated and labelled honestly. SHAILA is an early-warning and decision-support tool, not a replacement for official emergency authorities.</div>',
    unsafe_allow_html=True,
)

st.markdown(theme.render_footer(), unsafe_allow_html=True)

