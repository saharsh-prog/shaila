# SHAILA — Project Status & Technical Audit

> **Living document.** This is the running overview of what is built, what
> actually works, and what to do next. Updated as work lands.
>
> | | |
> |---|---|
> | **Last updated** | 2 September 2026 |
> | **Updated by** | Claude Code, at the team's request |
> | **Scope of this revision** | End-to-end audit of the ML pipeline — is it real or a showpiece? |

---

## 0. TL;DR for someone with two minutes

**The pipeline is real code that really runs.** Nothing is faked, hardcoded, or
stubbed at demo time. A RandomForest is genuinely trained, genuinely saved to
disk, and genuinely scored; the cache is asserted equal to the live model path
to 1e-6; the map draws real per-cell numbers. As *engineering*, it is sound and
better documented than most applied research projects.

**But the model is not doing what the pitch implies.** Four findings, in
descending order of importance:

| # | Finding | Severity |
|---|---|---|
| 1 | The model's main feature (`api_3d`) mathematically **contains** the quantity the label is defined from. It is substantially detecting rain that has already fallen, not forecasting rain that will fall. | 🔴 Critical |
| 2 | The headline **PR-AUC 0.8257 is measured at a 9.09% positive rate**, which is an artifact of 10:1 negative downsampling. At the true rate (0.02%), the same model scores **PR-AUC 0.359**. | 🟠 High |
| 3 | **There is no forecast path.** Every date is scored from *observed* weather. The system is a hindcast/nowcast, not an early-warning system, despite "Early Warning" being in the name. | 🟠 High |
| 4 | The README advertises **SHAP** and three other libraries that are neither installed nor imported. | 🟡 Medium |

None of these is fatal to the project. All four are *defensible if disclosed*
and *indefensible if a judge finds them first*. §6 has the fix order.

---

## 1. What is actually built

Verified by reading every file and executing the model — not from the README.

| Stage | File | Status | Evidence |
|---|---|---|---|
| 1 km grid | `app/grid_utils.py` | ✅ Working | 904 cells in `kamrup_metro_grid_1km.parquet` |
| Weather ingest | `app/weather_fetch.py` | ✅ Working | 1,332,432 rows, 19 weather points, 2018–2025 |
| Terrain / slope | `app/terrain_utils.py` | ✅ Working | `terrain_features.parquet`, 811 cells with DEM |
| Susceptibility | `app/susceptibility_utils.py` | ✅ Working | 4 classes + ASDMA hazard floor |
| Labelling | `app/labelling.py` | ⚠️ Works, but see §2 | 275 threshold-breaching weather-point-hours |
| Feature assembly | `app/features.py` | ✅ Working | Chunked join, avoids 31.9M-row blowup |
| Training | `app/train_trigger_model.py` | ✅ Working | RF + XGB, episode-grouped split |
| Model artifact | `models/random_forest_trigger_model.pkl` | ✅ Real | `RandomForestClassifier`, 100 trees, 5 features |
| Trigger cache | `build_trigger_cache.py` | ✅ Working | 55,518 rows, asserted == live path to 1e-6 |
| Prediction | `app/predict.py` | ✅ Working | `trigger × susceptibility` |
| Explanation | `app/explain.py` | ✅ Working | 19-key contract, no-DEM branch |
| IoT sim | `app/mqtt_sim.py` | ✅ Working, disclosed | Simulated, stated in UI |
| Frontend | `app/streamlit_app.py` + `app/views/` | ✅ Working | 4 pages, top nav |

**Confirmed model internals** (loaded from the `.pkl`, not from docs):

```
RandomForestClassifier(n_estimators=100, class_weight='balanced',
                       max_features='sqrt', random_state=42, max_depth=None)
n_features_in_ : 5
feature_names_ : soil_moisture_0_7, soil_moisture_7_28, temp_c, api_3d, api_7d
tree depth     : mean 21.7, max 29        ← fully grown, unpruned
leaves         : mean 274 per tree

feature importances
  soil_moisture_0_7   0.3287
  api_3d              0.2477
  soil_moisture_7_28  0.2334
  api_7d              0.1271
  temp_c              0.0630
```

**Verdict on "is it a showpiece?"** No. It is a working system. The code quality
is genuinely good — the memory-conscious chunked joins, the float32 rationale,
the cache-vs-live assertion, and the leak-avoidance comments in
`train_trigger_model.py` are all things most teams don't do. The problem is not
craft. It is that the *scientific* claim overreaches what the data supports.

---

## 2. Finding 1 — label leakage through `api_3d` 🔴

### The mechanism

The label is defined in `app/labelling.py`:

```python
rainfall_trigger = (precipitation_mm[t] >= 20) | (precip_3hr_mm[t] >= 60)
target_event     = rainfall_trigger & (slope_mean >= 15)
```

The features fed to the model are:

```python
FEATURES = ["soil_moisture_0_7", "soil_moisture_7_28", "temp_c", "api_3d", "api_7d"]
```

`train_trigger_model.py` asserts slope and elevation never reach `X`, and its
docstring calls these "the 5 confirmed non-leaking features." **That assertion
is about the wrong leak.** `api_3d` is built in `weather_fetch.py` as:

```python
df["api_3d"] = df.groupby("weather_point_id")["precipitation_mm"] \
                 .transform(lambda s: s.rolling(window=72, min_periods=1).sum())
```

pandas `.rolling()` **includes the current row**. So:

```
api_3d[t] = precipitation_mm[t] + precipitation_mm[t-1] + ... + precipitation_mm[t-71]
            └──────────┬──────────┘   └──────────────┬────────────────┘
            the label's own trigger      genuine antecedent history
```

`api_3d[t]` algebraically contains both `precip_1hr[t]` and `precip_3hr[t]` —
the exact two quantities the label is a threshold on. The model is not
predicting the label; it is partially *reading* it.

### Verified empirically

```
api_3d >= precip_3hr for all 1.33M rows : True   (necessarily — it's a superset)
api_3d >= precip_1hr for all 1.33M rows : True

rows where api_3d < 20mm (label mathematically impossible) : 931,137 (69.9%)
  actual positives there                                   : 0
  model's max probability there                            : 0.29
```

The model has learned an `api_3d` gate that shuts off exactly where the label
becomes arithmetically impossible. That gate is self-fulfilling.

### How much skill is leakage?

The decisive test: retrain identically, but **lag** the features so their window
closes *before* the label's window opens. Same model, same split method, same
9.09% positive rate.

| Feature set | PR-AUC | Lift over base rate |
|---|---|---|
| **Current hour (as shipped)** | **0.7985** | 9.5× |
| Lagged 1 h | 0.6703 | 8.0× |
| Lagged 3 h | 0.2510 | 3.0× |
| Lagged 6 h | 0.1530 | 1.8× |
| Lagged 12 h | 0.1433 | 1.7× |
| Lagged 24 h | 0.1150 | 1.4× |

*(My harness reproduces 0.7985 where the docs report 0.8257 — close enough to
confirm I am measuring the same thing; the small gap is my simplified
week-based episode grouping.)*

**Read the first two rows against the last.** Roughly **⅔ of the reported skill
disappears once the features can no longer see the labelling hour.** What
survives at 6–24 h lag (1.4–1.8× lift) is a genuine but weak antecedent-wetness
signal — soil moisture really does carry information about whether the ground is
primed. That real signal is worth keeping. It is just far smaller than 0.826
suggests.

### Why this is not a disaster

Two honest mitigations:

1. **`api_3d` is not *only* the label.** 71 of its 72 hours are legitimate
   antecedent history, and soil moisture (the top-importance feature) is a
   genuinely independent physical variable. This is contamination, not a pure
   identity function.
2. **A nowcast is still a useful product.** "Rain is falling now and this slope
   is primed to fail" has real operational value — that is what a *nowcast* is,
   and several real warning systems are exactly that. The problem is only that
   the project calls it prediction.

### What to do

**Minimum (1 hour, do this before any pitch):** disclose it. Add to the About
page and the training log: *"api_3d includes the current hour, so the trigger
model is a nowcast of conditions rather than a forecast. Reported PR-AUC
therefore measures detection, not lead time."* A judge who hears this from you
reads it as rigour. A judge who derives it themselves reads it as a hole.

**Proper fix (half a day):** add lagged variants and report both numbers.

```python
# in weather_fetch.py — shift so the window closes before the label hour
df["api_3d_lag3"] = df.groupby("weather_point_id")["api_3d"].shift(3)
```

Train on `*_lag3` and publish a two-column table: "detection (0 h)" vs
"forecast (3 h lead)". **Publishing the honest 0.25 alongside the 0.80 is a
stronger pitch than publishing 0.83 alone**, because it demonstrates you found
your own leak. Judges reward that.

---

## 3. Finding 2 — PR-AUC is measured at an inflated positive rate 🟠

The training set is downsampled 10:1 (`NEG_TO_POS_RATIO = 10`), giving a 9.09%
positive rate. All reported metrics come from that distribution. But PR-AUC —
unlike ROC-AUC — **is not invariant to prevalence**. The real world isn't 9.09%.

Same model, same features, evaluated on all 1,332,432 weather-point-hours:

| | Positive rate | PR-AUC |
|---|---|---|
| Reported (10:1 downsampled test fold) | 9.09% | **0.8257** |
| Measured at true prevalence | 0.0206% | **0.3590** |

The 0.359 is still **1,739× better than random** — the model is far from
useless. But 0.826 is not the number that describes operational performance, and
`F1 @ 0.5` at true prevalence is **0.11**, which is the number that tells you
what an operator's alert list would actually look like.

There is an irony worth noting: CLAUDE.md §4 rejects ROC-AUC for exactly the
right reason ("~2% positive class makes ROC-AUC misleading") and then reports a
PR-AUC that is misleading for the mirror-image reason. The instinct was correct;
it just wasn't carried all the way through.

**Fix (2 hours):** report both, in one table. Keep 0.826 as "PR-AUC on the
balanced evaluation set" and add "PR-AUC at operational prevalence: 0.359."
Also add **precision@k** — "of the top 20 cells we flag, how many were real?" —
which is the only metric an emergency operator actually cares about.

---

## 4. Finding 3 — there is no forecast path 🟠

Every risk number in the app is computed from **observed** weather:
`weather_hourly.parquet` is the Open-Meteo ERA5-Land **archive**. The date
picker spans 2018–2025 because that is the range of the historical record.

So the system answers *"given the weather that did happen on 30 May 2025, which
cells were at risk?"* — a hindcast. It cannot answer *"which cells are at risk
tomorrow?"*, because no forecast weather ever enters the pipeline. Combined with
Finding 1, the honest label for the current system is:

> **A hindcast risk-attribution tool** — not an early-warning system.

The architecture, though, is genuinely one step from being real. `predict.py`
takes a feature table and returns risk; it does not care whether the weather
came from an archive or a forecast. Open-Meteo's **forecast** API returns the
same variable names as the archive API from the same provider.

**Fix (1 day, highest value-per-hour in this document):** add a forecast fetch
alongside the archive fetch, and a "Live forecast" mode in the date picker
covering today → +7 days. This converts the project from *"we can explain the
past"* to *"we can warn about the future"* — which is the product's intended direction,
asks for, and it is achievable because the plumbing already exists.

⚠️ **Do not let me write the forecast endpoint URL from memory.** CLAUDE.md §11
is explicit that this project has been burned twice by fabricated sources. Open
`https://open-meteo.com/en/docs` and copy the forecast endpoint and parameter
names by hand, then paste them in. The archive endpoint already in
`docs/rainfall_soil_sources_verified.md` is verified; the forecast one is not
yet recorded anywhere in `docs/`.

---

## 5. Finding 4 — the README advertises four libraries the project does not use 🟡

`README.md:170` lists the tech stack as:

> Python · pandas · numpy · geopandas · rasterio · scikit-learn · **XGBoost** ·
> **SHAP** · Streamlit · Folium · **matplotlib** · paho-mqtt

Checked against `requirements.txt`, which contains exactly ten packages:

```
pandas, numpy, geopandas, shapely, scikit-learn,
streamlit, folium, streamlit-folium, paho-mqtt, pyarrow
```

| Claimed | In requirements? | Imported anywhere? | Reality |
|---|---|---|---|
| **SHAP** | ❌ No | ❌ No | Never used. CLAUDE.md §9 step 10 planned static SHAP plots; they were never built. `docs/img/` has 4 images, none of them SHAP |
| **XGBoost** | ❌ No | ⚠️ `train_trigger_model.py` only | Genuinely used *at training time* to pick a winner (it lost to RF). Not needed to run the app — but then the shipped `requirements.txt` cannot reproduce training |
| **rasterio** | ❌ No | ⚠️ terrain step only | Same: real, used upstream, absent from requirements |
| **matplotlib** | ❌ No | ❌ Not in app | Presumably used in notebooks |

Two separate issues here. The **honesty issue** is SHAP: the README claims
model explainability tooling that does not exist. The Insights page does have a
genuine per-feature explanation (deviation-from-median bars in `explain.py`),
which is real and defensible — it is just not SHAP, and should not be described
as SHAP.

The **reproducibility issue** is that `requirements.txt` was trimmed to runtime
dependencies only (commit `643f54d`), so a teammate cloning the repo cannot
re-run `app/train_trigger_model.py` — the import of `xgboost` will fail.

**Fix (30 minutes, do it with Tier 1):**
1. Delete `SHAP` and `matplotlib` from the README tech stack line.
2. Add a `requirements-dev.txt` with `xgboost`, `rasterio`, `matplotlib` and a
   one-line note that runtime and training dependencies differ.

If the team *wants* real SHAP, it is genuinely easy — a 5-feature
`TreeExplainer` on a RandomForest is a few lines, and the Insights page already
has a place to put the output. But claiming it while not having it is the worst
of the three options.

---

## 6. Recommended work order

Ordered by value per hour, given that the internal round has passed and the
system now needs to survive scrutiny rather than merely exist.

### Tier 1 — credibility (do these first, ~4.5 hours total)

| # | Task | Time | Why |
|---|---|---|---|
| 1.1 | **Disclose the `api_3d` leak** in About + `model_training_log.md` | 1 h | Turns your worst finding into evidence of rigour |
| 1.2 | **Report PR-AUC at both prevalences** | 2 h | Removes a number a judge could call inflated |
| 1.3 | **Add precision@20** | 1 h | The metric an actual operator cares about |
| 1.4 | **Cut SHAP/matplotlib from the README; add `requirements-dev.txt`** | 0.5 h | Stops the README claiming tooling that isn't there (§5) |

### Tier 2 — make the claim true (~2 days)

| # | Task | Time | Why |
|---|---|---|---|
| 2.1 | **Lagged-feature model, publish 0 h vs 3 h vs 6 h** | 0.5 d | Converts leakage from a flaw into a finding |
| 2.2 | **Open-Meteo forecast mode** (verify URL by hand) | 1 d | Makes "early warning" literally true |
| 2.3 | **Probability calibration** (`CalibratedClassifierCV`, isotonic) | 0.5 d | Fixes the step-function response; "72%" becomes meaningful |

### Tier 3 — better science (~3 days)

| # | Task | Time | Why |
|---|---|---|---|
| 3.1 | **TWI + distance-to-stream** | 1 d | Already in CLAUDE.md §4 priority list as #3/#5. Directly fixes the known Anil Nagar / Zoo Road blind spot — flat urban flooding that slope-only susceptibility cannot see |
| 3.2 | **Sensitivity analysis on the multipliers** | 0.5 d | The 0.20/0.45/0.70/0.90 weights are team-assigned and set the scale of every number on the map. Show the map at ±0.1 and state how much the ranking moves |
| 3.3 | **Leave-one-incident-out validation** | 1 d | With only 7 usable incidents, hold each out and ask whether its cell was flagged. Tiny *n*, but it is the only true ground truth in the project |
| 3.4 | **Resolve the SHAP claim** — see §5. Either implement it or cut it from the README | 0.5 d | The README currently advertises a library that is neither installed nor imported |

### Explicitly not recommended

Per CLAUDE.md §6, and I am not re-litigating these: deep learning, SMOTE/ADASYN,
Google Earth Engine, Optuna tuning, switching DEM source. None would help. The
binding constraint is **7 ground-truth incidents**, and no model architecture
fixes a label-quality problem.

---

## 7. Honest framing for the pitch

Two sentences that are defensible under questioning, and cost you nothing:

> "SHAILA computes 1 km-resolution slope-failure risk by multiplying a trained
> wetness-trigger model against a terrain susceptibility layer floored by
> ASDMA's official hazard list. Our trigger feature window includes the current
> hour, so we report it honestly as a **nowcast** — detection PR-AUC 0.83 at
> balanced prevalence, 0.36 at operational prevalence, falling to 0.25 at a
> 3-hour forecast lead."

That is a stronger position than claiming 0.83 as a forecast, because every
number in it survives being checked.

---

## 8. Open questions needing a human decision

1. **Does the team want the forecast mode?** It is the single change that makes
   the project's name accurate, but it needs someone to visually verify the
   Open-Meteo forecast endpoint (I must not write that URL from memory).
2. **Retrain, or disclose and move on?** Both are legitimate. Disclosure alone
   is ~4 hours; retraining with lagged features is ~half a day and produces a
   stronger story.
3. **The 3 ASDMA rows flagged "coordinate VERIFY"** are still unverified. They
   feed the hazard floor, so they affect real map output.
4. **Repo rename** `Srv99x/PRAVAH` → SHAILA. Breaks existing clones and any link
   already in the slide deck. Human call; not done.

---

## 9. Changelog

| Date | Change |
|---|---|
| 2 Sep 2026 | Document created. Full ML pipeline audit: `api_3d` label leakage (§2), prevalence-inflated PR-AUC (§3), absent forecast path (§4), README claiming uninstalled libraries (§5). **No code changed — audit only, at the team's request.** |

<!-- Append new rows above this comment, newest last.
     When a Tier task from §6 lands, add a row here AND flip its status in §1. -->
