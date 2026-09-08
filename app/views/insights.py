"""
app/views/insights.py
─────────────────────
Why a cell is at risk, and how much the model behind that claim can be
trusted. Three blocks: per-cell explanation, model performance, live
ingestion demo.

⚠ explain_cell() returns TWO DIFFERENT SHAPES.
   Success        → 19 keys.
   error_state == "no_dem" → ONLY 4 keys (grid_id, date, error_state, summary).
   Anything that reads the 19-key fields without branching on error_state
   first will KeyError on the 93 cells that lack DEM coverage. The branch
   below is not defensive padding — it is the contract.
"""

from datetime import date

import pandas as pd
import streamlit as st

from app import risk_engine as rk
from app import theme
from app.theme import C
from app.explain import explain_cell
from app.mqtt_sim import get_sensor_readings

theme.page_heading(
    "Insights",
    "Per-cell reasoning, model performance, and the live-ingestion interface.",
)

# ══════════════════════════════════════════════════════════════════════════════
# CELL SELECTION
# ══════════════════════════════════════════════════════════════════════════════

_min_date, _max_date = rk.available_date_range()
_max_date = max(_max_date, date(2026, 8, 31))

if (
    "shaila_date" not in st.session_state
    or st.session_state.shaila_date == date(2026, 6, 28)
):
    st.session_state.shaila_date = rk.DEFAULT_DATE

sel1, sel2 = st.columns([1, 2], gap="medium")

with sel1:
    explain_date = st.date_input(
        "Date",
        value=st.session_state.shaila_date,
        min_value=_min_date,
        max_value=_max_date,
        format="DD/MM/YYYY",
    )
    st.session_state.shaila_date = explain_date

gdf = rk.build_display_gdf(explain_date)

# Cells without DEM coverage can be explained, but only as "no data" — put the
# ones that actually carry a risk score at the top of the list instead.
valid = gdf[gdf["risk_probability"].notna()].sort_values(
    "risk_probability", ascending=False
)
options = list(valid["grid_id"]) + list(gdf.loc[gdf["no_dem"], "grid_id"])

with sel2:
    grid_id = st.selectbox(
        "Grid cell — ordered by risk on the selected date, highest first",
        options=options,
        index=0 if options else None,
    )

# ══════════════════════════════════════════════════════════════════════════════
# WHY IS THIS CELL AT RISK?
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div style="height:0.4rem"></div>', unsafe_allow_html=True)

if not grid_id:
    st.warning("No grid cells available for this date.")
else:
    try:
        # explain_cell requires an ISO STRING, not a date object.
        exp = explain_cell(grid_id, explain_date.strftime("%Y-%m-%d"))
    except FileNotFoundError as err:
        exp = None
        st.error(
            f"The trained model could not be loaded, so this cell cannot be "
            f"explained: {err}"
        )
    except ValueError as err:
        exp = None
        st.error(f"Could not explain {grid_id}: {err}")

    # ── THE BRANCH. Everything below the else: assumes the 19-key shape. ──
    if exp is None:
        pass

    elif exp["error_state"] == "no_dem":
        st.markdown(
            theme.panel(
                f"Why is {grid_id} at risk?",
                f'<p style="font-size:0.9rem;color:{C["text_soft"]};'
                f'line-height:1.65;margin:0">{exp["summary"]}<br><br>'
                f"This is one of the 93 cells in the 904-cell grid with no DEM "
                f"coverage. Its susceptibility multiplier is 0.0 and it renders "
                f'grey on the map. <b style="color:{C["text"]}">Grey is not '
                f"low risk</b> — it is an absence of evidence, and the honest "
                f"reading is that this cell is unassessed.</p>",
                count="No DEM",
            ),
            unsafe_allow_html=True,
        )

    else:
        sev = exp["severity"]
        risk_pct = exp["final_risk_score"] * 100
        trig_pct = exp["trigger_prob"] * 100

        left, right = st.columns([1.25, 1], gap="medium")

        with left:
            st.markdown(
                theme.panel(
                    f"Why is {grid_id} at risk?",
                    theme.stat_row([
                        theme.stat(f"{risk_pct:.1f}%", "final risk"),
                        theme.stat(f"{trig_pct:.1f}%", "trigger probability"),
                        theme.stat(
                            f"{exp['susceptibility_multiplier']:.2f}",
                            "susceptibility ×",
                        ),
                    ])
                    + theme.divider()
                    + f'<p style="font-size:0.9rem;color:{C["text"]};'
                      f'line-height:1.6;margin:0 0 0.6rem 0">'
                      f'{theme._esc(exp["summary"])}</p>'
                    + f'<p class="sh-note" style="margin:0">'
                      f'{theme._esc(exp["susceptibility_text"])}</p>',
                    count=theme.chip(sev),
                ),
                unsafe_allow_html=True,
            )

            # trigger_text is multi-line; markdown needs the breaks made explicit.
            trigger_lines = theme._esc(exp["trigger_text"]).split("\n")
            body = (
                f'<p class="sh-note" style="margin:0 0 0.6rem 0">'
                f"{trigger_lines[0]}</p>"
                + theme.diverging_bars(
                    [exp["feature_comparisons"][f] for f in
                     ["soil_moisture_0_7", "soil_moisture_7_28", "temp_c",
                      "api_3d", "api_7d"]]
                )
            )
            st.markdown(
                theme.panel(
                    "Conditions vs the historical norm",
                    body,
                    count=f"peak hour {exp['peak_timestamp'][11:16]}",
                ),
                unsafe_allow_html=True,
            )

        with right:
            floor = exp["floor_source"]
            floor_label = {
                "asdma": "ASDMA official hazard list",
                "incident": "Verified historical incident",
                "both": "ASDMA list + verified incident",
                None: "Not floored — terrain slope alone",
            }.get(floor, str(floor))

            st.markdown(
                theme.panel(
                    "Cell record",
                    theme.table(
                        ["Field", "Value"],
                        [
                            ["Grid ID",
                             f'<span style="font-family:ui-monospace,monospace;'
                             f'color:{C["text"]}">{grid_id}</span>'],
                            ["Date", exp["date"]],
                            ["Weather point", exp["weather_point_id"]],
                            ["Peak trigger hour",
                             exp["peak_timestamp"].replace("T", " ")],
                            ["Mean slope", f"{exp['slope_mean']:.1f}°"],
                            ["Susceptibility class",
                             exp["susceptibility_class"]],
                            ["Hazard floor",
                             theme.badge("applied", "warn")
                             if exp["hazard_floor_applied"]
                             else theme.badge("none", "ok")],
                            ["Floor source", floor_label],
                            ["Severity band", theme.chip(sev)],
                        ],
                        numeric_cols=(),
                    ),
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                theme.panel(
                    "Reading the two vocabularies",
                    f"""
<p class="sh-note" style="margin:0">
These are <b style="color:{C['text']}">different scales</b> and are easy to
confuse:<br><br>
<b style="color:{C['text']}">Susceptibility class</b> — Low / Moderate / High /
Very High. A property of the terrain. Does not change with the date.<br><br>
<b style="color:{C['text']}">Severity band</b> — Low / Medium / High / Severe.
A property of the <i>final risk score</i> on this date. Changes daily.<br><br>
A Very High susceptibility cell sits in the Low severity band on a dry day, and
that is correct behaviour, not a bug.
</p>
                    """,
                ),
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════════════
# MODEL PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div style="height:1.2rem"></div>', unsafe_allow_html=True)
st.markdown('<div class="sh-kicker">Model performance</div>',
            unsafe_allow_html=True)

m1, m2 = st.columns([1, 1], gap="medium")

with m1:
    st.markdown(
        theme.panel(
            "Held-out test results",
            theme.table(
                ["Model", "PR-AUC", "F1-macro"],
                [
                    [f'<b style="color:{C["text"]}">RandomForest</b> '
                     + theme.badge("shipped", "ok"),
                     '<b style="color:#E8EEF5">0.8257</b>',
                     '<b style="color:#E8EEF5">0.7640</b>'],
                    ["XGBoost", "0.7504", "0.8307"],
                ],
                numeric_cols=(1, 2),
            )
            + f'<p class="sh-note" style="margin-top:0.7rem">'
              f'<b style="color:{C["text_soft"]}">ROC-AUC is deliberately not '
              f"reported.</b> At a ~9% positive rate it flatters every model and "
              f"would misrepresent this one. RandomForest ships because it won on "
              f"PR-AUC, the metric that matters when positives are rare — XGBoost "
              f"scores higher on F1-macro, and that trade-off is a real one.</p>",
            count="fold 0 held out",
        ),
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        theme.panel(
            "How the split was made",
            f"""
<p class="sh-note" style="margin:0 0 0.7rem 0">
Rainfall-threshold labels make temporally adjacent hours near-duplicates, so a
random k-fold would leak. Runs of active hours are merged into
<b style="color:{C['text']}">61 storm episodes</b>, the group key is
<span style="font-family:ui-monospace,monospace">(year, episode_id)</span>, and
<span style="font-family:ui-monospace,monospace">StratifiedGroupKFold(n_splits=5,
shuffle=True, random_state=42)</span> holds out fold 0.
<b style="color:{C['text']}">0 groups appear on both sides</b> — asserted in code,
not assumed.
</p>
            """
            + theme.table(
                ["", "Rows", "Episodes", "Positive rate"],
                [
                    ["Train", "23,120", "103", "9.09%"],
                    ["Test", "5,777", "24", "9.09%"],
                ],
                numeric_cols=(1, 2, 3),
            ),
            count="127 groups",
        ),
        unsafe_allow_html=True,
    )

st.markdown(
    theme.panel(
        "Training data",
        theme.stat_row([
            theme.stat("28,897", "labelled rows"),
            theme.stat("2,627", "positives"),
            theme.stat("2,459", "threshold-derived"),
            theme.stat("168", "verified-incident"),
            theme.stat("19", "weather points"),
        ])
        + theme.divider()
        + f'<p class="sh-note" style="margin:0">Threshold rule for a synthetic '
          f'positive: <span style="font-family:ui-monospace,monospace;'
          f'color:{C["text"]}">precip_1hr &ge; 20 mm OR precip_3hr &ge; 60 mm, '
          f"AND slope_mean &ge; 15&deg;</span> — the intensity&ndash;duration "
          f"threshold from Dikshit &amp; Satyam (2019) for Kalimpong, the nearest "
          f"published Himalayan-foothill study. Negatives are stratified at 10:1. "
          f"Five features feed the model: soil moisture at 0&ndash;7 cm and "
          f"7&ndash;28 cm, temperature, and the 3-day and 7-day Antecedent "
          f"Precipitation Index.</p>",
        count="2018–2025",
    ),
    unsafe_allow_html=True,
)

st.markdown(
    theme.panel(
        "What these numbers do not cover",
        f"""
<p class="sh-note" style="margin:0">
&bull; <b style="color:{C['text']}">No probability calibration was applied.</b>
The trigger output is a RandomForest vote fraction, not a calibrated
probability. It responds close to a step function, which is why a mid-range
monsoon date can render an all-green map.<br>
&bull; <b style="color:{C['text']}">Susceptibility ranks by slope</b>, so it
systematically under-weights flat urban flooding. Anil Nagar and Zoo Road —
areas that flood in practice — sit in the Low band.<br>
&bull; <b style="color:{C['text']}">Metrics predating 28 Aug 2026 are void.</b>
Figures from before the split was rebuilt are not comparable to these and
should not be quoted alongside them.
</p>
        """,
    ),
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# SIMULATED IoT TELEMETRY
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div style="height:1.2rem"></div>', unsafe_allow_html=True)
st.markdown('<div class="sh-kicker">Live ingestion interface</div>',
            unsafe_allow_html=True)

st.warning(
    "**This telemetry is simulated.** No public village-level sensor network "
    "exists in India. These five virtual hill-site nodes demonstrate the MQTT "
    "ingestion interface a real feed would drop into — the transport and the "
    "panel are real, the readings are generated.",
    icon="📡",
)

streaming = st.toggle("Ingest live IoT telemetry", value=False)


def _render_sensors(readings) -> None:
    """One row per node. Rainfall drives the colour, since it is the trigger."""
    rows = []
    for s in readings:
        rain = float(s["rainfall_mm_hr"])
        # Bands mirror the map's severity ramp so a heavy-rain node reads as
        # hot in the same visual language as a hot grid cell.
        if rain >= 20:
            tone = theme.SEVERITY_COLORS["Severe"]
        elif rain >= 10:
            tone = theme.SEVERITY_COLORS["High"]
        elif rain >= 4:
            tone = theme.SEVERITY_COLORS["Medium"]
        else:
            tone = theme.SEVERITY_COLORS["Low"]

        rows.append([
            f'<span style="font-family:ui-monospace,monospace;color:{C["text"]}">'
            f'{s["sensor_id"]}</span>',
            f'<span style="font-family:ui-monospace,monospace">{s["grid_id"]}</span>',
            str(s["label"]),
            f'<b style="color:{tone}">{rain:.1f}</b>',
            f'{float(s["soil_moisture_pct"]):.1f}',
            f'{float(s["water_level_m"]):.2f}',
            f'<span style="color:{C["text_muted"]}">{s["timestamp"]}</span>',
        ])

    st.markdown(
        theme.panel(
            "Node telemetry",
            theme.table(
                ["Node", "Grid cell", "Site", "Rain mm/hr",
                 "Soil moisture %", "Water level m", "Received"],
                rows,
                numeric_cols=(3, 4, 5),
            ),
            count=f"{len(readings)} nodes · simulated",
        ),
        unsafe_allow_html=True,
    )


if streaming:
    # A fragment reruns on its own timer instead of blocking the script in a
    # sleep loop — the rest of the page, and the nav bar, stay responsive.
    @st.fragment(run_every="3s")
    def _live_panel() -> None:
        _render_sensors(get_sensor_readings())

    _live_panel()
else:
    _render_sensors(get_sensor_readings())
    st.caption("Showing a single snapshot. Toggle above to stream at 3-second intervals.")
