"""
app/views/about.py
──────────────────
Method, provenance, limitations, team.

This page exists because the project has twice been burned by fabricated
sources. Every URL below was copied from docs/ — none was reconstructed from
memory, and a source with no recorded URL is listed WITHOUT one rather than
with a plausible guess. If you add a row here, add its URL to docs/ first.
"""

import pandas as pd
import streamlit as st

from app import risk_engine as rk
from app import theme
from app.theme import C

theme.page_heading(
    "Method & Data",
    "How the system works, where the data comes from, and what it cannot do.",
)

# ══════════════════════════════════════════════════════════════════════════════
# NAME + SCOPE
# ══════════════════════════════════════════════════════════════════════════════

a1, a2 = st.columns([1, 1], gap="medium")

with a1:
    st.markdown(
        theme.panel(
            "The name",
            f"""
<p class="sh-note" style="margin:0">
<b style="color:{C['text']};font-size:1.1rem;letter-spacing:0.1em">SHAILA</b>
&nbsp;<span style="color:{C['accent']};font-size:1rem">शैल</span><br><br>
Sanskrit for <i>rock</i> or <i>mountain</i>, representing the hilly terrain of Kamrup Metropolitan where rapid extreme precipitation causes hyper-local flash floods and sudden urban inundations across hill slopes and floodplains.
</p>
            """,
        ),
        unsafe_allow_html=True,
    )

with a2:
    st.markdown(
        theme.panel(
            "Scope",
            theme.table(
                ["Field", "Value"],
                [
                    ["District", "Kamrup Metropolitan, Assam"],
                    ["Grid", "904 cells at 1 km × 1 km"],
                    ["Date range", "2018-01-01 to 2026-08-31"],
                    ["Timestep", "Hourly weather, daily peak surfaced"],
                    ["Weather points", "19"],
                ],
            ),
        ),
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# METHOD
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="sh-kicker" style="margin-top:0.8rem">Method</div>',
            unsafe_allow_html=True)

st.markdown(
    theme.panel(
        "Pipeline",
        theme.table(
            ["Stage", "What happens", "Output"],
            [
                ["1 · Grid",
                 "A 1 km vector grid is generated over the district boundary "
                 "and clipped to it.",
                 "904 cells"],
                ["2 · Terrain",
                 "Zonal statistics over the local SRTM/CartoDEM give mean slope "
                 "and elevation per cell.",
                 "slope_mean, elevation_mean"],
                ["3 · Susceptibility",
                 "Cells are ranked into four classes by slope, then "
                 "<i>floored</i> to at least High wherever ASDMA lists a "
                 "vulnerable location or a verified incident occurred.",
                 "Low / Moderate / High / Very High"],
                ["4 · Weather",
                 "Hourly rainfall, soil moisture at two depths and temperature "
                 "are fetched per weather point and rolled into 3-day and "
                 "7-day antecedent precipitation indices.",
                 "5 model features"],
                ["5 · Labels",
                 "Positives come from an intensity–duration threshold on "
                 "sloping cells, plus verified incident dates. Negatives are "
                 "stratified at 10:1.",
                 "28,897 rows"],
                ["6 · Model",
                 "RandomForest (100 trees, class-balanced, seed 42) trained on "
                 "episode-grouped folds.",
                 "trigger probability"],
                ["7 · Cache",
                 "Every (weather point, date) trigger probability is "
                 "precomputed and asserted equal to the live model to 1e-6.",
                 "55,518 rows"],
                ["8 · Serve",
                 "The app multiplies the cached trigger by the static "
                 "susceptibility multiplier. No model call at demo time.",
                 "per-cell risk"],
            ],
        ),
    ),
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# DATA SOURCES
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="sh-kicker" style="margin-top:0.8rem">Data sources</div>',
            unsafe_allow_html=True)


def _link(url: str) -> str:
    return (f'<a href="{url}" target="_blank" '
            f'style="color:{C["accent"]};text-decoration:none;'
            f'font-size:0.78rem;word-break:break-all">{url}</a>')


IN_USE = [
    ["Open-Meteo ERA5-Land archive",
     "Hourly rainfall, soil moisture (0–7 cm, 7–28 cm), temperature",
     theme.badge("in use", "ok"),
     _link("https://archive-api.open-meteo.com/v1/archive")],
    ["Local SRTM / CartoDEM",
     "Slope and elevation, via rasterio zonal statistics",
     theme.badge("in use", "ok"),
     '<span style="color:#6B7A8D;font-size:0.78rem">Local raster — '
     'no public endpoint recorded in docs/</span>'],
    ["ASDMA vulnerable-location list",
     "Transcribed to data/raw/asdma_vulnerable_locations.csv (47 rows). "
     "Applies the susceptibility hazard floor.",
     theme.badge("in use", "ok"),
     '<span style="color:#6B7A8D;font-size:0.78rem">Transcribed from the '
     'official assessment; 3 rows are flagged &ldquo;coordinate VERIFY&rdquo; '
     'and need a human check</span>'],
    ["Verified incident record",
     "8 documented flash flood incidents, 2022-06-14 to 2026-07-16. "
     "Used for ground-truth validation and hazard floor.",
     theme.badge("in use", "ok"),
     _link("https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1987753")],
    ["GADM administrative boundary",
     "District polygon used to clip the grid",
     theme.badge("in use", "ok"),
     _link("https://gadm.org")],
]

EVALUATED = [
    ["GSMaP_ISRO Rain (MOSDAC)", "0.1° hourly rainfall, gauge-adjusted",
     theme.badge("verified", "ok"),
     _link("https://www.mosdac.gov.in/gsmap-isro-rain")],
    ["NASA GPM IMERG", "30-minute global rainfall",
     theme.badge("verified", "ok"),
     _link("https://gpm.nasa.gov/data/imerg")],
    ["IMD 0.25° gridded daily rainfall", "Long Indian historical baseline",
     theme.badge("verified", "ok"),
     _link("https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html")],
    ["Copernicus ERA5-Land (CDS)", "Same reanalysis, direct CDS access",
     theme.badge("verified", "ok"),
     _link("https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land")],
    ["NASA SMAP L4 SPL4SMGP", "9 km 3-hourly surface/root-zone soil moisture",
     theme.badge("verified", "ok"),
     _link("https://nsidc.org/data/spl4smgp/versions/8")],
    ["Terrain hazard records", "Terrain and flood-susceptibility reference layers",
     theme.badge("verified", "ok"),
     _link("https://bhukosh.gsi.gov.in/Bhukosh/Public")],
    ["Terrain hazard portal", "Terrain hazard reference portal",
     theme.badge("verified", "ok"),
     _link("https://bhusanket.gsi.gov.in/LS_hazard.html")],
]

REJECTED = [
    ["MOSDAC SMAP soil moisture / SWI",
     "Official bounding box is 5–24°N — it excludes Guwahati at 26.14°N. "
     "Using it here would have been silently wrong.",
     theme.badge("rejected", "bad"), ""],
    ["Google Earth Engine backend",
     "GCP auth overhead and a new mental model for no necessary gain, against "
     "a hard deadline.",
     theme.badge("rejected", "bad"), ""],
    ["SMOTE / ADASYN oversampling",
     "Synthesising fake flood hazard locations on spatially autocorrelated "
     "geodata is methodologically weak and hard to defend.",
     theme.badge("rejected", "bad"), ""],
    ["Deep learning as the core model",
     "Would overfit ~2,600 positives and destroy the interpretability the "
     "explanation panel depends on.",
     theme.badge("rejected", "bad"), ""],
]

st.markdown(
    theme.panel(
        "In the pipeline",
        theme.table(["Source", "What it provides", "Status", "Reference"], IN_USE),
        count=f"{len(IN_USE)} sources",
    ),
    unsafe_allow_html=True,
)

st.markdown(
    theme.panel(
        "Verified secondary data sources",
        theme.table(["Source", "What it provides", "Status", "Reference"], EVALUATED)
        + f'<p class="sh-note" style="margin-top:0.7rem">These are real, checked '
          f"sources that did not make the pilot — mostly because each needs its "
          f"own login and Open-Meteo collapsed rainfall and soil moisture into a "
          f"single keyless call. They are the obvious next ingest.</p>",
        count=f"{len(EVALUATED)} sources",
    ),
    unsafe_allow_html=True,
)

st.markdown(
    theme.panel(
        "Considered and rejected",
        theme.table(["Item", "Why not", "Status", ""], REJECTED),
    ),
    unsafe_allow_html=True,
)

LIMITS = [
    ("Weather resolution",
     "ERA5-Land is natively coarser than 1 km; weather fields are mapped onto the grid."),
    ("Telemetry status",
     "The Insights telemetry panel is simulated and labelled as such; it is an interface demonstration."),
    ("Slope-focused susceptibility",
     "Terrain susceptibility is stronger for hill-slope flash-flood risk than flat urban flooding."),
    ("Partial DEM coverage",
     "93 of 904 cells have no DEM coverage and are shown as No Data, not low risk."),
    ("No probability calibration",
     "The trigger output is a Random Forest vote fraction rather than a calibrated probability."),
    ("Single-district scope",
     "Built and validated for Kamrup Metropolitan only; these specific numbers do not generalise automatically."),
    ("Boundary area discrepancy",
     "The GADM polygon gives ~904 km² against a 1,528 km² figure cited by some "
     "official sources. Visual inspection confirms the polygon covers central "
     "Guwahati, the Fatasil/Kalapahar/Narengi hill zones and the riverfront — "
     "every area the hazard record is situated in. Noted, not resolved."),
]

lim_left, lim_right = st.columns(2, gap="medium")
for i, (title, body) in enumerate(LIMITS):
    with (lim_left if i % 2 == 0 else lim_right):
        st.markdown(theme.card(title, body), unsafe_allow_html=True)
        st.markdown('<div style="height:0.7rem"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VERIFIED INCIDENTS
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="sh-kicker" style="margin-top:0.4rem">'
            'Verified incident record</div>', unsafe_allow_html=True)

incidents = rk.load_incidents()

if incidents.empty:
    st.info("data/raw/verified_incidents.csv is not present in this checkout.")
else:
    rows = []
    for _, inc in incidents.iterrows():
        when = (
            inc["date"].strftime("%d %b %Y")
            if pd.notna(inc["date"]) else "date unknown"
        )
        rows.append([
            when,
            f'<b style="color:{C["text"]}">{inc["location"]}</b>',
            f'{float(inc["latitude"]):.4f}, {float(inc["longitude"]):.4f}',
            str(inc.get("notes", "") or ""),
        ])
    st.markdown(
        theme.panel(
            "Documented incidents used for labelling and the hazard floor",
            theme.table(
                ["Date", "Location", "Coordinates", "Notes"],
                rows,
                numeric_cols=(2,),
            )
            + f'<p class="sh-note" style="margin-top:0.7rem">Casualty figures '
              f"appear in the free-text notes only — there is no numeric "
              f"casualty column, so no total is computed or claimed here.</p>",
            count=f"{len(incidents)} incidents",
        ),
        unsafe_allow_html=True,
    )

