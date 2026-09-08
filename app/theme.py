"""
app/theme.py
────────────
Design tokens and reusable HTML components for the SHAILA dashboard.

Everything visual lives here so the four pages stay consistent and a colour
change happens in exactly one place.  No page should hardcode a hex value.

Colour policy (this is not decoration — it is an accessibility decision)
───────────────────────────────────────────────────────────────────────
The four severity bands use a hazard ramp that a colour-blind viewer cannot
fully separate by hue alone: green↔orange sits at ΔE 2.7 under protanopia.
Conventional hazard ramps (green/amber/orange/red) simply cannot clear that
bar — so severity is ALWAYS carried by a second channel as well:

  • on the map      — fill opacity rises with the band (0.28 → 0.80) and the
                      border thickens, so "hot" cells read as hot in greyscale
  • in the UI       — a colour swatch never appears without its text label
  • in tables       — the severity word is present in its own column

That is what makes the palette legal rather than merely pretty.  If you change
SEVERITY_COLORS, re-run the validator before shipping.
"""

from __future__ import annotations

import base64
import functools
import html as _html
from pathlib import Path

import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# BRAND
# ══════════════════════════════════════════════════════════════════════════════

APP_NAME    = "SHAILA"
APP_DEVANAGARI = "शैल"
APP_TAGLINE = "Flash-Flood Early Warning System"
APP_SUBTITLE = "Kamrup Metropolitan District, Assam"
APP_MEANING = "shaila · शैल · flash-flood early warning"

# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND IMAGE LOADER
# ══════════════════════════════════════════════════════════════════════════════

@functools.lru_cache(maxsize=1)
def get_background_css() -> str:
    """Return CSS url data URI for the background image, or empty string."""
    img_path = Path(__file__).resolve().parent / "assets" / "background.png"
    if img_path.exists():
        try:
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
                return f"url('data:image/png;base64,{b64}')"
        except Exception:
            pass
    return "none"


@functools.lru_cache(maxsize=1)
def get_hero_background_css() -> str:
    """Return CSS url data URI for the hero background image."""
    img_path = Path(__file__).resolve().parent / "assets" / "hero_banner.jpg"
    if img_path.exists():
        try:
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
                return f"url('data:image/jpeg;base64,{b64}')"
        except Exception:
            pass
    return "url('https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=1600&q=80')"

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS (Glassmorphic Dark Palette)
# ══════════════════════════════════════════════════════════════════════════════

C = {
    # surfaces — pale blue-gray canvas with high-contrast navy ink
    "bg":             "#EEF3F8",
    "surface":        "#FFFFFF",
    "surface_raised": "#F8FBFD",
    "surface_hover":  "#EAF2F8",
    # lines
    "border":         "#D5E0EA",
    "border_strong":  "#B7C9D8",
    # ink
    "text":           "#102A43",
    "text_soft":      "#38546B",
    "text_muted":     "#667D91",
    # brand accent — ocean blue accent
    "accent":         "#0284C7",
    "accent_dim":     "rgba(2, 132, 199, 0.15)",
}

# Severity ramp. High-clarity luminous tones that pop against frosted glass.
SEVERITY_COLORS = {
    "Low":     "#10B981",
    "Medium":  "#F59E0B",
    "High":    "#F97316",
    "Severe":  "#EF4444",
    "No Data": "#64748B",
}

# Secondary encoding — the channel that survives colour-blindness.
SEVERITY_OPACITY = {
    "Low":     0.28,
    "Medium":  0.45,
    "High":    0.62,
    "Severe":  0.80,
    "No Data": 0.14,
}

SEVERITY_ORDER = ["Severe", "High", "Medium", "Low", "No Data"]

SEVERITY_RANGE = {
    "Low":     "< 25%",
    "Medium":  "25 – 50%",
    "High":    "50 – 75%",
    "Severe":  "> 75%",
    "No Data": "no DEM",
}


def severity_color(sev: str) -> str:
    """Hex for a severity label, falling back to the No-Data grey."""
    return SEVERITY_COLORS.get(str(sev), SEVERITY_COLORS["No Data"])


def severity_opacity(sev: str) -> float:
    """Map fill opacity for a severity label."""
    return SEVERITY_OPACITY.get(str(sev), SEVERITY_OPACITY["No Data"])


# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════

def inject_theme() -> None:
    """Inject the global glassmorphic theme. Call once per page render."""
    bg_img = get_background_css()
    st.markdown(
        f"""
<style>
/* ── base app container with forest background ─────────────────────────── */
.stApp {{
    background: {C['bg']} !important;
}}

[data-testid="stAppViewContainer"],
[data-testid="stMain"] {{
    background: {C['bg']} !important;
}}

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stSidebar"] {{
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: {C['text']} !important;
}}

[data-testid="stMainBlockContainer"] {{
    /* Clear navigation bar and left floating dock */
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 1560px;
}}

[data-testid="stHeader"] {{
    background: transparent !important;
    border-bottom: none !important;
}}

body, p, span, li, label {{ color: {C['text_soft']}; }}
h1, h2, h3, h4, h5 {{
    color: {C['text']} !important;
    letter-spacing: -0.015em;
    text-shadow: none;
}}

/* ── legacy floating navigation (disabled; the app uses the top bar) ───── */
.sh-floating-dock {{
    display: none !important;
}}

.sh-dock-item {{
    width: 44px;
    height: 44px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94A3B8;
    background: transparent;
    text-decoration: none !important;
    position: relative;
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}}

.sh-dock-item i {{
    font-size: 20px;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}}

/* Hover state */
.sh-dock-item:hover {{
    color: #FFFFFF;
    background: rgba(255, 255, 255, 0.10);
    transform: scale(1.08);
}}

/* Active state — vibrant turquoise / cyan solid pill matching the reference image */
.sh-dock-item.active {{
    background: #2DD4BF !important;
    color: #022C22 !important;
    box-shadow: 0 0 20px rgba(45, 212, 191, 0.55), 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    transform: scale(1.04);
}}
.sh-dock-item.active:hover {{
    color: #022C22 !important;
}}

/* Tooltip on hover */
.sh-dock-item::after {{
    content: attr(data-tooltip);
    position: absolute;
    left: 56px;
    background: rgba(10, 16, 24, 0.90);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    color: #FFFFFF;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 0.35rem 0.65rem;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.14);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
    transform: translateX(-6px);
    transition: all 0.18s ease;
}}

.sh-dock-item:hover::after {{
    opacity: 1;
    transform: translateX(0);
}}

/* ── Top right hamburger ───────────────────────────────────────────────── */
[data-testid="stSidebarCollapsedControl"] {{
    position: fixed !important;
    top: 20px !important;
    right: 28px !important;
    left: auto !important;
    z-index: 999999 !important;
    display: block !important;
}}

[data-testid="stSidebarCollapsedControl"] button {{
    width: 44px !important;
    height: 44px !important;
    border-radius: 14px !important;
    background: rgba(13, 20, 30, 0.72) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    color: #F8FAFC !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}

[data-testid="stSidebarCollapsedControl"] button:hover {{
    background: rgba(255, 255, 255, 0.15) !important;
    color: #2DD4BF !important;
    transform: translateY(-1px);
    box-shadow: 0 10px 28px rgba(45, 212, 191, 0.25) !important;
}}

[data-testid="stSidebarCollapsedControl"] button svg {{
    width: 20px !important;
    height: 20px !important;
    color: currentColor !important;
}}

.sh-top-hamburger {{
    position: fixed;
    right: 28px;
    top: 20px;
    z-index: 999998;
}}

.sh-hamburger-btn {{
    width: 44px;
    height: 44px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(13, 20, 30, 0.72);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.14);
    color: #F8FAFC;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.16);
    cursor: pointer;
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}}

.sh-hamburger-btn i {{
    font-size: 18px;
    line-height: 1;
}}

.sh-hamburger-btn:hover {{
    background: rgba(255, 255, 255, 0.15);
    color: #2DD4BF;
    transform: translateY(-1px);
    box-shadow: 0 10px 28px rgba(45, 212, 191, 0.25);
}}

/* ── Start here CTA cards ───────────────────────────────────────────────── */
.sh-cta-card {{
    display: flex;
    align-items: center;
    gap: 0.95rem;
    padding: 1.0rem 1.35rem;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%),
                rgba(14, 24, 38, 0.65);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 14px;
    color: #F8FAFC !important;
    text-decoration: none !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.14);
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}}
.sh-cta-card:hover {{
    border-color: rgba(45, 212, 191, 0.55);
    background: linear-gradient(135deg, rgba(45, 212, 191, 0.20) 0%, rgba(45, 212, 191, 0.05) 100%),
                rgba(20, 36, 56, 0.85);
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(45, 212, 191, 0.25);
    color: #FFFFFF !important;
}}
.sh-cta-icon {{
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 12px;
    background: rgba(45, 212, 191, 0.15);
    color: #2DD4BF;
    font-size: 1.2rem;
    flex-shrink: 0;
}}
.sh-cta-text {{
    font-size: 0.94rem;
    font-weight: 600;
    color: #F8FAFC;
    letter-spacing: 0.01em;
}}

/* ── Sidebar (Control drawer) ──────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background: rgba(8, 14, 22, 0.75) !important;
    backdrop-filter: blur(28px) saturate(190%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(190%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.12) !important;
    box-shadow: 10px 0 36px rgba(0, 0, 0, 0.45) !important;
}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
    color: #CBD5E1;
    font-size: 0.86rem;
}}



/* ── widgets & inputs ───────────────────────────────────────────────────── */
[data-testid="stWidgetLabel"] label p {{
    color: {C['text_soft']} !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}

[data-baseweb="input"],
[data-baseweb="select"] > div {{
    background: rgba(13, 22, 33, 0.65) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 10px !important;
    color: #FFFFFF !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.25), 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    transition: all 0.2s ease !important;
}}
[data-baseweb="input"]:focus-within,
[data-baseweb="select"] > div:focus-within {{
    border-color: {C['accent']} !important;
    box-shadow: 0 0 16px rgba(56, 189, 248, 0.3) !important;
}}

[data-baseweb="popover"],
[data-baseweb="menu"] {{
    background: rgba(11, 18, 28, 0.94) !important;
    backdrop-filter: blur(24px) saturate(190%) !important;
    -webkit-backdrop-filter: blur(24px) saturate(190%) !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 12px !important;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6) !important;
}}

/* ── buttons ────────────────────────────────────────────────────────────── */
button[kind="primary"],
.stButton > button {{
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.03) 100%),
                rgba(18, 30, 46, 0.70) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 10px !important;
    color: #F8FAFC !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 0.5rem 0.85rem !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.18) !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}
button[kind="primary"]:hover,
.stButton > button:hover {{
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.28) 0%, rgba(56, 189, 248, 0.08) 100%),
                rgba(24, 42, 66, 0.85) !important;
    border-color: rgba(56, 189, 248, 0.55) !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 20px rgba(56, 189, 248, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
    transform: translateY(-1px);
}}
button[kind="primary"]:active,
.stButton > button:active {{
    transform: translateY(1px);
}}

/* ── page links (CTA buttons) ───────────────────────────────────────────── */
[data-testid="stPageLink-NavLink"] {{
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%),
                rgba(14, 24, 38, 0.65) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 12px !important;
    padding: 0.85rem 1.1rem !important;
    transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
}}
[data-testid="stPageLink-NavLink"]:hover {{
    border-color: rgba(56, 189, 248, 0.45) !important;
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.18) 0%, rgba(56, 189, 248, 0.04) 100%),
                rgba(20, 36, 56, 0.85) !important;
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(56, 189, 248, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.22) !important;
}}

/* ── native metrics ─────────────────────────────────────────────────────── */
[data-testid="stMetric"] {{
    background: rgba(13, 22, 33, 0.55) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    border-radius: 12px !important;
    padding: 0.9rem 1.1rem !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.10) !important;
}}
[data-testid="stMetricValue"] {{
    color: #FFFFFF !important;
    font-weight: 700 !important;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}}
[data-testid="stMetricLabel"] {{
    color: {C['text_muted']} !important;
    font-size: 0.74rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}}

/* ── dataframe ──────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    background: rgba(11, 18, 28, 0.65) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 12px !important;
    overflow: hidden;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3) !important;
}}

/* ── expander / alerts ──────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    background: rgba(13, 22, 33, 0.55) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25) !important;
}}
[data-testid="stAlert"] {{
    background: rgba(16, 26, 40, 0.68) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.16) !important;
    border-radius: 12px !important;
    color: #F8FAFC !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
}}

/* ── the map fills its container cleanly ────────────────────────────────── */
iframe[title="streamlit_folium.st_folium"] {{
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.45);
}}

/* ── SHAILA components ──────────────────────────────────────────────────── */
.sh-brand {{
    display: flex; align-items: baseline; gap: 0.8rem;
    padding-bottom: 0.5rem;
}}
.sh-brand-name {{
    font-size: 1.65rem; font-weight: 800; letter-spacing: 0.15em;
    color: #FFFFFF; line-height: 1;
    text-shadow: 0 0 20px rgba(255, 255, 255, 0.35);
}}
.sh-brand-dev {{
    font-size: 1.05rem; color: {C['accent']}; font-weight: 600;
    text-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
}}
.sh-brand-tag {{
    font-size: 0.80rem; color: {C['text_muted']};
    letter-spacing: 0.06em; text-transform: uppercase;
}}

.sh-panel {{
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.01) 100%),
                rgba(13, 21, 32, 0.62);
    backdrop-filter: blur(18px) saturate(180%);
    -webkit-backdrop-filter: blur(18px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 1.15rem 1.25rem;
    margin-bottom: 0.95rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.14);
    transition: all 0.25s ease;
}}
.sh-panel-title {{
    font-size: 0.74rem; font-weight: 700; letter-spacing: 0.13em;
    text-transform: uppercase; color: {C['text_muted']};
    margin-bottom: 0.9rem;
    display: flex; justify-content: space-between; align-items: center;
}}
.sh-panel-title .sh-count {{
    color: {C['text_soft']}; font-weight: 600; letter-spacing: 0.04em;
}}

/* stat grid */
.sh-stats {{ display: flex; flex-wrap: wrap; gap: 0 0.8rem; }}
.sh-stat {{
    flex: 1 1 0; min-width: 95px;
    padding: 0.4rem 0.2rem 0.75rem 0;
}}
.sh-stat-value {{
    font-size: 1.7rem; font-weight: 800; color: #FFFFFF;
    line-height: 1.1;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}}
.sh-stat-value.accent {{
    color: {C['accent']};
    text-shadow: 0 0 18px rgba(56, 189, 248, 0.45);
}}
.sh-stat-label {{
    font-size: 0.70rem; color: {C['text_muted']};
    text-transform: uppercase; letter-spacing: 0.08em;
    margin-top: 0.25rem;
}}
.sh-divider {{
    height: 1px; background: rgba(255, 255, 255, 0.10);
    margin: 0.65rem 0 0.95rem 0;
}}

/* severity distribution bars */
.sh-bar-row {{
    display: flex; align-items: center; gap: 0.65rem;
    margin-bottom: 0.6rem;
}}
.sh-bar-label {{
    font-size: 0.78rem; color: {C['text']};
    width: 165px; flex-shrink: 0; font-weight: 600;
}}
.sh-bar-track {{
    flex: 1; height: 10px; background: rgba(0, 0, 0, 0.08);
    border-radius: 5px; overflow: hidden;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.15);
}}
.sh-bar-fill {{
    display: block !important;
    height: 100% !important; border-radius: 5px;
    box-shadow: 0 0 8px currentColor;
    transition: width 0.3s ease;
}}
.sh-bar-count {{
    font-size: 0.80rem; color: {C['text_soft']};
    width: 44px; text-align: right; flex-shrink: 0;
    font-variant-numeric: tabular-nums;
    font-weight: 700;
}}

/* Top navigation buttons */
.sh-top-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.4rem 0 0.6rem 0;
    margin-bottom: 0.4rem;
}}
.sh-top-logo {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1.35rem;
    font-weight: 800;
    color: {C['accent']};
    letter-spacing: 0.04em;
}}
.sh-top-logo-sub {{
    font-size: 0.82rem;
    font-weight: 500;
    color: {C['text_muted']};
    margin-left: 0.4rem;
    padding-left: 0.6rem;
    border-left: 1px solid {C['border']};
}}
div[data-testid="stButton"] button[kind="primary"] {{
    background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: 1px solid #38BDF8 !important;
    box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35) !important;
    border-radius: 8px !important;
}}
div[data-testid="stButton"] button[kind="secondary"] {{
    background: rgba(255, 255, 255, 0.8) !important;
    color: #38546B !important;
    font-weight: 500 !important;
    border: 1px solid #D5E0EA !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}}
div[data-testid="stButton"] button[kind="secondary"]:hover {{
    background: #EAF2F8 !important;
    color: #0284C7 !important;
    border-color: #0284C7 !important;
}}

/* severity chip — swatch + label, never colour alone */
.sh-chip {{
    display: inline-flex; align-items: center; gap: 0.45rem;
    font-size: 0.82rem; color: #F8FAFC;
    background: rgba(255, 255, 255, 0.06);
    padding: 0.15rem 0.55rem;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.10);
}}
.sh-dot {{
    width: 9px; height: 9px; border-radius: 2px;
    display: inline-block; flex-shrink: 0;
    box-shadow: 0 0 8px currentColor;
}}

/* hero */
.sh-hero {{
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.09) 0%, rgba(34, 197, 94, 0.05) 45%, rgba(13, 21, 32, 0.65) 100%);
    backdrop-filter: blur(24px) saturate(190%);
    -webkit-backdrop-filter: blur(24px) saturate(190%);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 18px;
    padding: 2.5rem 2.3rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.20);
}}
.sh-hero h1 {{
    font-size: 2.8rem; font-weight: 800; letter-spacing: 0.18em;
    margin: 0 0 0.2rem 0; color: #FFFFFF;
    text-shadow: 0 0 24px rgba(255, 255, 255, 0.4);
}}
.sh-hero .sh-sub {{
    font-size: 1.05rem; color: {C['accent']}; font-weight: 600;
    margin-bottom: 0.95rem;
    text-shadow: 0 0 14px rgba(56, 189, 248, 0.4);
}}
.sh-hero p {{
    font-size: 0.98rem; color: {C['text_soft']}; line-height: 1.7;
    max-width: 64ch; margin: 0;
}}

/* generic card used on Home / Insights / About */
.sh-card {{
    background: #FFFFFF;
    border: 1px solid #D5E0EA;
    border-radius: 8px;
    padding: 1.25rem 1.35rem;
    height: 100%;
    box-shadow: 0 5px 16px rgba(16, 42, 67, 0.08);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}}
.sh-card:hover {{
    transform: translateY(-2px);
    border-color: #0284C7;
    box-shadow: 0 10px 24px rgba(2, 132, 199, 0.14);
}}
.sh-card h4 {{
    font-size: 0.96rem; font-weight: 700; margin: 0 0 0.55rem 0;
    color: #102A43;
}}
.sh-card p {{
    font-size: 0.88rem; color: {C['text_soft']};
    line-height: 1.65; margin: 0;
}}
.sh-kicker {{
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.13em;
    text-transform: uppercase; color: {C['accent']};
    margin-bottom: 0.4rem;
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.35);
}}

/* ── MOCKUP DESIGN EXTENSIONS (LIGHT THEME) ────────────────────────────── */
.sh-top-header {{
    display: flex; justify-content: space-between; align-items: center;
    background: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
    padding: 0.8rem 2.2rem; margin: -1.5rem -2.5rem 1.25rem -2.5rem;
}}
.sh-top-logo {{
    display: flex; align-items: center; gap: 0.75rem;
    font-size: 1.4rem; font-weight: 800; color: #0F172A; letter-spacing: 0.12em;
}}
.sh-top-logo svg {{
    color: #0284C7; filter: drop-shadow(0 2px 6px rgba(2, 132, 199, 0.3));
}}
.sh-top-nav {{
    display: flex; gap: 2rem; font-size: 0.9rem; font-weight: 600;
}}
.sh-top-nav a {{
    color: #475569; text-decoration: none; transition: color 0.2s ease;
}}
.sh-top-nav a:hover, .sh-top-nav a.active {{
    color: #0284C7; font-weight: 700;
}}
.sh-nav-cta {{
    background: #0284C7 !important; color: #FFFFFF !important; border-radius: 6px;
    padding: 0.48rem 0.8rem; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.22);
}}
.sh-nav-cta:hover {{ background: #0369A1 !important; color: #FFFFFF !important; }}

/* Hero Banner */
.sh-hero-banner {{
    position: relative;
    min-height: 245px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 3.4rem 3.2rem;
    margin-bottom: 1.1rem;
    box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
    overflow: hidden;
}}
.sh-hero-content {{
    max-width: 750px; position: relative; z-index: 2;
}}
.sh-hero-title {{
    font-size: 2.6rem; font-weight: 800; color: #FFFFFF; line-height: 1.15;
    margin-bottom: 0.5rem; text-shadow: 0 4px 20px rgba(0, 0, 0, 0.8);
}}
.sh-hero-sub {{
    font-size: 1.35rem; font-weight: 700; color: #38BDF8; margin-bottom: 0.7rem;
    text-shadow: 0 2px 14px rgba(0, 0, 0, 0.8);
}}
.sh-hero-desc {{
    font-size: 1.05rem; color: #F1F5F9; margin-bottom: 2rem; font-weight: 500;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.8);
}}
.sh-hero-actions {{
    display: flex; gap: 1rem;
}}
.sh-btn-primary {{
    background: #0284C7;
    color: #FFFFFF !important; font-weight: 700; border-radius: 8px;
    padding: 0.8rem 1.8rem; text-decoration: none; display: inline-flex; align-items: center;
    box-shadow: 0 6px 20px rgba(2, 132, 199, 0.4); transition: transform 0.2s ease, background 0.2s ease;
}}
.sh-btn-primary span, .sh-btn-secondary span {{
    color: #FFFFFF !important;
}}
.sh-btn-primary:hover {{
    transform: translateY(-2px); background: #0369A1;
}}
.sh-btn-secondary {{
    background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(12px);
    color: #FFFFFF !important; font-weight: 600; border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.25);
    padding: 0.8rem 1.8rem; text-decoration: none; display: inline-flex; align-items: center;
    transition: transform 0.2s ease, background 0.2s ease;
}}
.sh-btn-secondary:hover {{
    transform: translateY(-2px); background: rgba(30, 41, 59, 0.95);
}}
.sh-btn-secondary span {{
    color: #FFFFFF !important;
}}

/* Feature Pills Row */
.sh-feature-pills {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; margin-bottom: 1.1rem;
}}
.sh-pill-card {{
    background: #FFFFFF;
    border: 1px solid #D5E0EA;
    border-radius: 0; padding: 0.75rem 1rem;
    display: flex; align-items: center; gap: 1rem;
    box-shadow: none; transition: transform 0.2s ease, border-color 0.2s ease;
}}
.sh-pill-card:hover {{ transform: translateY(-3px); border-color: #0284C7; box-shadow: 0 10px 24px rgba(2, 132, 199, 0.12); }}
.sh-pill-icon {{
    width: 42px; height: 42px; border-radius: 10px; background: #E0F2FE;
    display: flex; align-items: center; justify-content: center; font-size: 1.5rem; flex-shrink: 0;
    border: 1px solid #BAE6FD;
}}
.sh-pill-title {{ font-size: 0.94rem; font-weight: 700; color: #0F172A; line-height: 1.2; }}
.sh-pill-sub {{ font-size: 0.76rem; color: #64748B; margin-top: 0.2rem; }}

/* KPI Cards Grid */
.sh-kpi-grid {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.7rem; margin-bottom: 1.2rem;
}}
.sh-kpi-card {{
    border-radius: 4px; padding: 1rem; min-height: 105px;
    display: flex; flex-direction: column; justify-content: space-between;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08); border: 1px solid rgba(255,255,255,0.2);
    position: relative; overflow: hidden;
}}
.sh-kpi-card.risk-severe {{
    background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%); color: #FFFFFF;
}}
.sh-kpi-card.risk-high {{
    background: linear-gradient(135deg, #EA580C 0%, #C2410C 100%); color: #FFFFFF;
}}
.sh-kpi-card.risk-moderate {{
    background: linear-gradient(135deg, #D97706 0%, #B45309 100%); color: #FFFFFF;
}}
.sh-kpi-card.risk-low {{
    background: linear-gradient(135deg, #059669 0%, #047857 100%); color: #FFFFFF;
}}
.sh-kpi-card.blue-metric {{
    background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%); color: #FFFFFF;
}}
.sh-kpi-header {{
    font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.92;
}}
.sh-kpi-body {{
    display: flex; align-items: center; gap: 0.85rem; margin-top: 0.6rem;
}}
.sh-kpi-val {{ font-size: 1.5rem; font-weight: 800; line-height: 1.1; }}
.sh-kpi-sub {{ font-size: 0.82rem; opacity: 0.88; margin-top: 0.2rem; }}

/* Circular Feature Badges */
.sh-badges-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; margin: 1.1rem 0;
}}
.sh-badge-circle-item {{
    display: flex; flex-direction: column; align-items: center; text-align: center;
}}
.sh-circle-icon {{
    width: 66px; height: 66px; border-radius: 50%;
    background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
    box-shadow: 0 8px 22px rgba(2, 132, 199, 0.35);
    display: flex; align-items: center; justify-content: center; font-size: 1.85rem;
    margin-bottom: 0.6rem; border: 3px solid #FFFFFF;
}}
.sh-circle-title {{ font-size: 0.9rem; font-weight: 700; color: #0F172A; margin-bottom: 0.25rem; }}
.sh-circle-desc {{ font-size: 0.76rem; color: #64748B; line-height: 1.35; }}

/* Email Subscribe Block */
.sh-subscribe-card {{
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    border: 1px solid #334155; border-radius: 16px;
    padding: 1.8rem; margin-top: 1.5rem; box-shadow: 0 12px 32px rgba(15, 23, 42, 0.15);
}}
.sh-sub-title {{ font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.35rem; }}
.sh-sub-desc {{ font-size: 0.86rem; color: #94A3B8; margin-bottom: 1.1rem; }}
.sh-sub-form {{ display: flex; gap: 0.7rem; }}
.sh-sub-input {{
    flex: 1; background: #1E293B; border: 1px solid #475569;
    border-radius: 8px; padding: 0.7rem 1.1rem; color: #FFFFFF; font-size: 0.9rem;
}}
.sh-sub-btn {{
    background: #0284C7; color: #FFFFFF; font-weight: 700; border: none; border-radius: 8px;
    padding: 0.7rem 1.5rem; font-size: 0.9rem; cursor: pointer; transition: background 0.2s ease;
}}
.sh-sub-btn:hover {{ background: #0369A1; }}

/* Footer Bar */
.sh-footer {{
    background: #0B132B; border-top: 1px solid #1E293B;
    padding: 1.15rem 2.5rem; margin: 2.2rem -2.5rem -1rem -2.5rem;
    display: flex; justify-content: space-between; align-items: center;
    font-size: 0.86rem; color: #94A3B8;
}}
.sh-footer-links {{ display: flex; gap: 1.8rem; }}
.sh-footer-links a {{ color: #CBD5E1; text-decoration: none; font-weight: 500; }}
.sh-footer-links a:hover {{ color: #38BDF8; }}
.sh-footer-socials {{ display: flex; gap: 1.2rem; font-size: 1.15rem; color: #CBD5E1; }}

/* ── operational dashboard components ─────────────────────────────────── */
.sh-panel {{
    background: #FFFFFF !important; border: 1px solid {C['border']} !important;
    border-radius: 8px !important; box-shadow: 0 5px 16px rgba(16, 42, 67, 0.06) !important;
    backdrop-filter: none !important; -webkit-backdrop-filter: none !important;
}}
.sh-panel-title {{ color: {C['text_muted']} !important; }}
.sh-panel-title .sh-count, .sh-note {{ color: {C['text_soft']} !important; }}
.sh-stat-value, .sh-card h4 {{ color: {C['text']} !important; text-shadow: none !important; }}
.sh-stat-label, .sh-bar-label, .sh-bar-count {{ color: {C['text_muted']} !important; }}
.sh-divider {{ background: {C['border']} !important; }}
.sh-bar-track {{ background: {C['surface_hover']} !important; }}
.sh-chip {{ color: {C['text']} !important; background: {C['surface_hover']} !important; border-color: {C['border']} !important; }}
.sh-badge {{ color: {C['text']} !important; }}
.sh-table {{ color: {C['text_soft']} !important; border-color: {C['border']} !important; }}
.sh-table th {{ background: {C['surface_hover']} !important; color: {C['text']} !important; }}
.sh-table td {{ border-color: {C['border']} !important; }}
[data-testid="stSidebar"] {{ background: #FFFFFF !important; border-right: 1px solid {C['border']} !important; box-shadow: 6px 0 20px rgba(16, 42, 67, 0.08) !important; }}
[data-testid="stSidebar"] * {{ color: {C['text_soft']} !important; }}
[data-baseweb="input"], [data-baseweb="select"] > div {{ background: #FFFFFF !important; color: {C['text']} !important; border-color: {C['border']} !important; box-shadow: none !important; }}
[data-baseweb="input"] input, [data-baseweb="select"] input {{ color: {C['text']} !important; }}
button[kind="primary"], .stButton > button {{ background: #FFFFFF !important; color: {C['text']} !important; border-color: {C['border_strong']} !important; box-shadow: 0 3px 10px rgba(16, 42, 67, 0.08) !important; }}
button[kind="primary"]:hover, .stButton > button:hover {{ background: {C['surface_hover']} !important; color: {C['accent']} !important; border-color: {C['accent']} !important; }}

/* Navbar controls: distinct from content buttons and easy to scan. */
[data-testid="stElementContainer"][class*="st-key-nav_"] .stButton > button {{
    background: #173B55 !important;
    background-color: #173B55 !important;
    color: #EAF7FC !important;
    border: 1px solid #285B78 !important;
    border-radius: 7px !important;
    box-shadow: 0 3px 10px rgba(16, 42, 67, 0.14) !important;
    font-weight: 700 !important;
}}
[data-testid="stElementContainer"][class*="st-key-nav_"] .stButton > button p {{
    color: #EAF7FC !important;
}}
[data-testid="stElementContainer"][class*="st-key-nav_"] .stButton > button:hover {{
    background: #245A73 !important;
    background-color: #245A73 !important;
    color: #FFFFFF !important;
    border-color: #4CC9F0 !important;
}}
[data-testid="stElementContainer"][class*="st-key-nav_"] .stButton > button:hover p {{ color: #FFFFFF !important; }}
[data-testid="stElementContainer"][class*="st-key-nav_"] .stButton > button:focus-visible {{
    outline: 3px solid rgba(76, 201, 240, 0.45) !important;
    outline-offset: 2px !important;
}}

.sh-section-heading {{
    display: flex; justify-content: space-between; align-items: end; gap: 1rem;
    margin: 1.65rem 0 0.75rem 0;
}}
.sh-section-heading h3 {{ margin: 0; font-size: 1.15rem; color: {C['text']} !important; }}
.sh-section-heading p {{ margin: 0; color: {C['text_muted']}; font-size: 0.82rem; text-align: right; }}
.sh-page-hero {{
    position: relative; overflow: hidden; margin: 0.65rem 0 1.25rem;
    padding: 1.25rem 1.45rem 1.3rem; border: 1px solid {C['border']};
    border-radius: 10px; background: #FFFFFF; box-shadow: 0 5px 16px rgba(16, 42, 67, 0.06);
}}
.sh-page-hero::before {{
    content: ""; position: absolute; inset: 0 auto 0 0; width: 7px; background: {C['accent']};
}}
.sh-page-hero.insights {{ background: linear-gradient(110deg, #E9F7FC 0%, #FFFFFF 62%); }}
.sh-page-hero.insights::before {{ background: #0284C7; }}
.sh-page-hero.method {{ background: linear-gradient(110deg, #F0F8F2 0%, #FFFFFF 62%); }}
.sh-page-hero.method::before {{ background: #16845B; }}
.sh-page-hero.risk {{ background: linear-gradient(110deg, #FFF8ED 0%, #FFFFFF 62%); }}
.sh-page-hero.risk::before {{ background: #D97706; }}
.sh-page-hero-kicker {{
    color: {C['text_muted']}; font-size: 0.68rem; font-weight: 800;
    letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.35rem;
}}
.sh-page-hero h2 {{ margin: 0 !important; color: {C['text']} !important; font-size: 1.48rem !important; }}
.sh-page-hero p {{ margin: 0.4rem 0 0 !important; color: {C['text_soft']} !important; font-size: 0.9rem; }}
.sh-capability-grid, .sh-status-grid, .sh-transparency-grid {{
    display: grid; gap: 0.75rem;
}}
.sh-capability-grid {{ grid-template-columns: repeat(4, 1fr); margin-bottom: 1.2rem; }}
.sh-status-grid {{ grid-template-columns: repeat(5, 1fr); }}
.sh-transparency-grid {{ grid-template-columns: repeat(2, 1fr); }}
.sh-capability, .sh-status, .sh-transparency-card {{
    background: #FFFFFF; border: 1px solid {C['border']}; border-radius: 8px;
    box-shadow: 0 5px 16px rgba(16, 42, 67, 0.06);
}}
.sh-capability {{ padding: 1rem; min-height: 122px; }}
.sh-capability-icon {{
    width: 34px; height: 34px; display: grid; place-items: center;
    border-radius: 8px; background: #E4F4FB; color: {C['accent']}; font-size: 1.1rem;
    margin-bottom: 0.7rem;
}}
.sh-capability-title {{ color: {C['text']}; font-weight: 750; font-size: 0.88rem; margin-bottom: 0.3rem; }}
.sh-capability-text {{ color: {C['text_soft']}; font-size: 0.78rem; line-height: 1.45; }}
.sh-status {{ padding: 0.9rem 1rem; min-height: 92px; }}
.sh-status-value {{ color: {C['text']}; font-size: 1.2rem; font-weight: 800; line-height: 1.2; }}
.sh-status-label {{ color: {C['text_muted']}; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.07em; margin-top: 0.35rem; }}
.sh-status-note {{ color: {C['text_muted']}; font-size: 0.69rem; margin-top: 0.35rem; }}
.sh-pipeline {{
    display: flex; align-items: stretch; gap: 0.35rem; margin: 0.7rem 0 1rem;
    overflow-x: auto; padding-bottom: 0.25rem;
}}
.sh-pipeline-step {{
    flex: 1 0 132px; background: #F8FBFD; border: 1px solid {C['border']};
    border-radius: 7px; padding: 0.8rem 0.7rem; text-align: center; position: relative;
}}
.sh-pipeline-step:not(:last-child)::after {{
    content: "→"; position: absolute; right: -0.68rem; top: 50%; transform: translateY(-50%);
    z-index: 2; color: {C['accent']}; background: {C['bg']}; padding: 0 0.15rem; font-weight: 800;
}}
.sh-pipeline-index {{ color: {C['accent']}; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.1em; }}
.sh-pipeline-label {{ color: {C['text']}; font-size: 0.78rem; font-weight: 700; line-height: 1.3; margin-top: 0.35rem; }}
.sh-formula {{
    background: #E9F7FC; border: 1px solid #B9E4F3; border-radius: 8px;
    padding: 1rem 1.2rem; color: {C['text']}; text-align: center; font-weight: 800;
}}
.sh-formula small {{ display: block; margin-top: 0.4rem; color: {C['text_soft']}; font-size: 0.76rem; font-weight: 500; }}
.sh-transparency-card {{ padding: 1rem 1.1rem; }}
.sh-transparency-card h4 {{ color: {C['text']}; margin: 0 0 0.65rem; font-size: 0.9rem; }}
.sh-transparency-card ul {{ margin: 0; padding-left: 1.1rem; color: {C['text_soft']}; font-size: 0.8rem; line-height: 1.7; }}
.sh-limitations {{
    background: #FFF9ED; border: 1px solid #F2D49A; border-left: 4px solid #D97706;
    border-radius: 8px; padding: 1rem 1.15rem; color: {C['text_soft']}; font-size: 0.84rem; line-height: 1.6;
}}
.sh-limitations strong {{ color: {C['text']}; }}

/* ── calm operational mode ────────────────────────────────────────────── */
*, *::before, *::after {{
    animation: none !important;
    transition: none !important;
}}
.sh-top-header {{
    position: sticky; top: 0; z-index: 1000; margin-bottom: 0.35rem;
    box-shadow: 0 2px 8px rgba(16, 42, 67, 0.07);
}}
.stPageLink, [data-testid="stPageLink-NavLink"] {{
    min-height: 2.35rem !important; align-items: center !important;
}}
[data-testid="stPageLink-NavLink"] {{
    justify-content: center !important; background: #FFFFFF !important;
    border: 1px solid {C['border']} !important; border-radius: 6px !important;
    color: {C['text_soft']} !important; padding: 0.45rem 0.55rem !important;
    box-shadow: none !important; text-decoration: none !important;
}}
[data-testid="stPageLink-NavLink"] p, [data-testid="stPageLink-NavLink"] span {{
    color: {C['text_soft']} !important; font-weight: 650 !important;
}}
[data-testid="stPageLink-NavLink"]:hover {{
    background: {C['surface_hover']} !important; border-color: {C['accent']} !important;
}}
[data-testid="stPageLink-NavLink"]:hover p, [data-testid="stPageLink-NavLink"]:hover span {{
    color: {C['accent']} !important;
}}
[data-testid="stPageLink-NavLink"][aria-current="page"] {{
    background: #E4F4FB !important; border-color: {C['accent']} !important;
}}
[data-testid="stPageLink-NavLink"][aria-current="page"] p,
[data-testid="stPageLink-NavLink"][aria-current="page"] span {{ color: {C['accent']} !important; }}
.stPageLink:last-child [data-testid="stPageLink-NavLink"] {{
    background: {C['accent']} !important; border-color: {C['accent']} !important;
}}
.stPageLink:last-child [data-testid="stPageLink-NavLink"] p,
.stPageLink:last-child [data-testid="stPageLink-NavLink"] span {{ color: #FFFFFF !important; }}
.sh-top-nav a:hover {{ transform: none !important; }}
.sh-capability:hover, .sh-status:hover, .sh-card:hover {{
    transform: none !important; box-shadow: 0 5px 16px rgba(16, 42, 67, 0.06) !important;
}}
.stTabs [data-baseweb="tab-list"] {{ gap: 0.25rem; border-bottom: 1px solid {C['border']}; }}
.stTabs [data-baseweb="tab"] {{ color: {C['text_soft']} !important; font-weight: 650; }}
.stTabs [aria-selected="true"] {{ color: {C['accent']} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background: {C['accent']} !important; }}
.stAlert {{ background: #F8FBFD !important; border: 1px solid {C['border']} !important; color: {C['text']} !important; }}
.stCaption {{ color: {C['text_muted']} !important; }}

@media (max-width: 850px) {{
    [data-testid="stMainBlockContainer"] {{ padding-left: 1rem !important; padding-right: 1rem !important; }}
    .sh-top-header {{ margin-left: -1rem; margin-right: -1rem; padding: 0.75rem 1rem; }}
    .sh-top-nav {{ gap: 0.8rem; font-size: 0.76rem; flex-wrap: wrap; justify-content: flex-end; }}
    .sh-top-nav .sh-nav-cta {{ display: none; }}
    .sh-feature-pills, .sh-capability-grid, .sh-status-grid, .sh-transparency-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .sh-hero-banner {{ padding: 2.4rem 1.4rem; min-height: 260px; }}
    .sh-hero-title {{ font-size: 2rem; }}
    .sh-hero-sub {{ font-size: 1.05rem; }}
    .sh-section-heading {{ display: block; }}
    .sh-section-heading p {{ text-align: left; margin-top: 0.3rem; }}
}}
@media (max-width: 560px) {{
    .sh-feature-pills, .sh-capability-grid, .sh-status-grid, .sh-transparency-grid {{ grid-template-columns: 1fr; }}
    .sh-top-logo {{ font-size: 1.05rem; }}
    .sh-top-nav a:nth-child(3) {{ display: none; }}
    .sh-hero-actions {{ flex-wrap: wrap; }}
}}
</style>
        """,
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# HTML COMPONENT BUILDERS
# Each returns a string; the caller passes it to st.markdown(..., True).
# ══════════════════════════════════════════════════════════════════════════════

def _esc(text) -> str:
    """Escape anything that reaches an HTML component."""
    return _html.escape(str(text))


def brand_header() -> str:
    """The SHAILA wordmark used at the top of every page."""
    return (
        '<div class="sh-brand">'
        f'<span class="sh-brand-name">{APP_NAME}</span>'
        f'<span class="sh-brand-dev">{APP_DEVANAGARI}</span>'
        f'<span class="sh-brand-tag">{_esc(APP_TAGLINE)}</span>'
        "</div>"
    )


def panel(title: str, body: str, count: str | None = None) -> str:
    """A bordered panel with an uppercase title and arbitrary HTML body."""
    if count:
        right_content = count if ("<" in count and ">" in count) else _esc(count)
        right = f'<span class="sh-count">{right_content}</span>'
    else:
        right = ""
    return (
        '<div class="sh-panel">'
        f'<div class="sh-panel-title"><span>{_esc(title)}</span>{right}</div>'
        f"{body}"
        "</div>"
    )


def stat(value: str, label: str, accent: bool = False) -> str:
    """One number + caption inside a .sh-stats flex row."""
    cls = "sh-stat-value accent" if accent else "sh-stat-value"
    return (
        '<div class="sh-stat">'
        f'<div class="{cls}">{_esc(value)}</div>'
        f'<div class="sh-stat-label">{_esc(label)}</div>'
        "</div>"
    )


def stat_row(stats: list[str]) -> str:
    """Wrap stat() outputs into a responsive grid."""
    return f'<div class="sh-stats">{"".join(stats)}</div>'


def divider() -> str:
    return '<div class="sh-divider"></div>'


def chip(severity: str) -> str:
    """Colour swatch + text label. Never emit the swatch on its own."""
    return (
        '<span class="sh-chip">'
        f'<span class="sh-dot" style="background:{severity_color(severity)}"></span>'
        f"{_esc(severity)}</span>"
    )


def severity_bars(counts: dict, total: int) -> str:
    """
    Horizontal distribution of cells across the severity bands.

    A bar chart rather than a donut: these are ordered magnitude values that
    get compared against each other, and a bar baseline reads that far better
    than angles do.
    """
    rows = []
    denom = max(total, 1)

    severity_labels = {
        "Severe": "Severe - Evacuate",
        "High": "High - Alert",
        "Medium": "Medium - Monitor",
        "Low": "Low - Normal Monitoring",
        "No Data": "No Data",
    }

    for sev in SEVERITY_ORDER:
        n = int(counts.get(sev, 0))
        pct = 100.0 * n / denom
        color = severity_color(sev)
        display_label = severity_labels.get(sev, sev)
        rows.append(
            '<div class="sh-bar-row">'
            f'<span class="sh-bar-label">{_esc(display_label)}</span>'
            '<span class="sh-bar-track">'
            f'<span class="sh-bar-fill" style="display:block;width:{pct:.1f}%;'
            f'background:{color} !important;height:100%;border-radius:4px"></span></span>'
            f'<span class="sh-bar-count">{n:,}</span>'
            "</div>"
        )
    return "".join(rows)


def legend() -> str:
    """Risk-band legend. Always paired with its numeric range."""
    rows = []
    for sev in ["Low", "Medium", "High", "Severe", "No Data"]:
        rows.append(
            '<div class="sh-bar-row">'
            f'<span class="sh-dot" style="background:{severity_color(sev)}"></span>'
            f'<span class="sh-bar-label" style="width:auto;flex:1">{_esc(sev)}</span>'
            f'<span class="sh-bar-count" style="width:auto">{_esc(SEVERITY_RANGE[sev])}</span>'
            "</div>"
        )
    return "".join(rows)


DIVERGING_ABOVE = "#EF4444"   # above the historical median — pushes risk up
DIVERGING_BELOW = "#38BDF8"   # below the historical median — pushes risk down
DIVERGING_MID   = "rgba(255, 255, 255, 0.25)"   # neutral glass midpoint

# Deviations beyond this are clipped so one extreme feature cannot flatten
# the other four into invisible stubs.
_DEV_CLIP_PCT = 150.0


def diverging_bars(rows: list[dict]) -> str:
    """
    Feature values as signed deviation from their historical monthly median.

    This is polarity data — "wetter than normal" versus "drier than normal" —
    so it gets a diverging encoding: two opposed hues with a neutral gray
    midpoint, never a single ramp. Bars are scaled by PERCENT deviation, which
    is what makes m³/m³, °C and mm comparable on one axis at all.

    Each row needs: label, actual, baseline, difference, unit.
    """
    prepared = []
    for r in rows:
        base = float(r["baseline"])
        diff = float(r["difference"])
        if base != 0:
            pct = 100.0 * diff / abs(base)
        elif diff == 0:
            pct = 0.0
        else:
            # A zero median with a non-zero reading is an infinite ratio.
            # Clip rather than divide — common in dry months where the
            # 3-day antecedent rainfall median is genuinely 0 mm.
            pct = _DEV_CLIP_PCT if diff > 0 else -_DEV_CLIP_PCT
        prepared.append((r, max(-_DEV_CLIP_PCT, min(_DEV_CLIP_PCT, pct))))

    span = max((abs(p) for _, p in prepared), default=1.0) or 1.0

    out = [
        f'<div style="display:flex;justify-content:space-between;'
        f'font-size:0.66rem;letter-spacing:0.08em;text-transform:uppercase;'
        f'color:{C["text_muted"]};margin-bottom:0.5rem">'
        f'<span>&#9664; below median</span>'
        f'<span>above median &#9654;</span></div>'
    ]

    for r, pct in prepared:
        width = 50.0 * abs(pct) / span      # half the track at most
        above = pct > 0
        color = DIVERGING_ABOVE if above else DIVERGING_BELOW
        # Bars grow outward from the 50% midline.
        left = 50.0 if above else 50.0 - width
        bar = (
            f'<span style="position:absolute;left:{left:.2f}%;width:{width:.2f}%;'
            f"top:0;bottom:0;background:{color};border-radius:3px\"></span>"
            if abs(pct) > 0.05
            else ""
        )
        sign = "+" if r["difference"] > 0 else ""
        out.append(
            '<div style="margin-bottom:0.62rem">'
            f'<div style="display:flex;justify-content:space-between;'
            f'font-size:0.78rem;margin-bottom:0.22rem">'
            f'<span style="color:{C["text"]}">{_esc(r["label"])}</span>'
            f'<span style="color:{C["text_soft"]};font-variant-numeric:tabular-nums">'
            f'{float(r["actual"]):.2f} {_esc(r["unit"])} '
            f'<span style="color:{color}">({sign}{float(r["difference"]):.2f})</span>'
            "</span></div>"
            f'<div style="position:relative;height:9px;background:{C["surface_raised"]};'
            f'border-radius:3px">{bar}'
            f'<span style="position:absolute;left:50%;top:-2px;bottom:-2px;'
            f'width:1px;background:{DIVERGING_MID}"></span>'
            "</div></div>"
        )

    out.append(
        f'<p class="sh-note" style="margin:0.4rem 0 0 0">Bars show percent '
        f"deviation from the 2018&ndash;2025 median for this weather point in "
        f"this calendar month, clipped at &plusmn;{_DEV_CLIP_PCT:.0f}%. Absolute "
        f"values and differences are printed above each bar.</p>"
    )
    return "".join(out)


def card(title: str, body: str, kicker: str | None = None) -> str:
    """Titled content card used across Home / Insights / About."""
    k = f'<div class="sh-kicker">{_esc(kicker)}</div>' if kicker else ""
    return (
        f'<div class="sh-card">{k}'
        f"<h4>{_esc(title)}</h4>"
        f"<p>{body}</p>"
        "</div>"
    )


def badge(text: str, kind: str = "ok") -> str:
    """Status pill — 'ok' | 'warn' | 'bad'."""
    return f'<span class="sh-badge {kind}">{_esc(text)}</span>'


def table(headers: list[str], rows: list[list[str]], numeric_cols=()) -> str:
    """
    Static HTML table.

    Used instead of st.dataframe where the content is prose-ish and needs
    inline markup (badges, chips) that a DataFrame cannot carry.
    """
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = []
    for row in rows:
        tds = []
        for i, cell in enumerate(row):
            cls = ' class="num"' if i in numeric_cols else ""
            # Cells are pre-built HTML from callers in this repo, not user input.
            tds.append(f"<td{cls}>{cell}</td>")
        body.append(f"<tr>{''.join(tds)}</tr>")
    return (
        f'<table class="sh-table"><thead><tr>{head}</tr></thead>'
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def page_heading(title: str, subtitle: str = "") -> None:
    """Standard page header with the shared top navigation."""
    t_lower = title.lower()
    if title.startswith("About") or "method" in t_lower:
        active_page = "Method & Data"
    elif "risk" in t_lower:
        active_page = "Risk Map"
    elif "insight" in t_lower:
        active_page = "Insights"
    else:
        active_page = title

    render_top_header(active_page)
    hero_class = "method" if active_page == "Method & Data" else "insights" if active_page == "Insights" else "risk"
    kicker = {
        "method": "Transparency and provenance",
        "insights": "Model explanation and evidence",
        "risk": "Operational forecast",
    }[hero_class]
    st.markdown(
        f'<section class="sh-page-hero {hero_class}">'
        f'<div class="sh-page-hero-kicker">{kicker}</div>'
        f'<h2>{_esc(title)}</h2>'
        f'<p>{_esc(subtitle)}</p>'
        f'</section>',
        unsafe_allow_html=True,
    )


# Inline SVGs — no CDN, no font, no breakage
_SVG_HOME = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9.5 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
_SVG_MARKER = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>'
_SVG_INSIGHT = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="8" y2="14"/><line x1="14" y1="9" x2="14" y2="14"/></svg>'
_SVG_INFO = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
_SVG_BURGER = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>'


def render_floating_navbar(active_page: str = "Home") -> None:
    """Render the floating vertical navbar on the left and hamburger on top-right."""

    def _item(href: str, svg: str, tooltip: str, is_active: bool) -> str:
        cls = "sh-dock-item active" if is_active else "sh-dock-item"
        return f'<a href="{href}" target="_self" class="{cls}" data-tooltip="{tooltip}">{svg}</a>'

    dock_html = (
        '<div class="sh-floating-dock">'
        + _item("/", _SVG_HOME, "Home", active_page == "Home")
        + _item("/risk_map", _SVG_MARKER, "Risk Map", active_page == "Risk Map")
        + _item("/insights", _SVG_INSIGHT, "Insights", active_page == "Insights")
        + _item("/about", _SVG_INFO, "About", active_page == "About")
        + '</div>'
    )

    st.markdown(dock_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MOCKUP LAYOUT HELPERS (MATCHING REFERENCE DESIGN)
# ══════════════════════════════════════════════════════════════════════════════

def render_top_header(active_page: str = "Home") -> None:
    """Render a branded header with reliable Streamlit router buttons."""
    act_lower = active_page.lower()
    if "method" in act_lower or "about" in act_lower:
        norm_active = "Method & Data"
    elif "risk" in act_lower:
        norm_active = "Risk Map"
    elif "insight" in act_lower:
        norm_active = "Insights"
    else:
        norm_active = "Home"

    st.markdown(
        """
<div class="sh-top-header">
  <div class="sh-top-logo">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 19 9.5 8l4 5 2.5-3 5 9H3Z"/><path d="m9.5 8 2-3 2 3"/></svg>
    <span>SHAILA</span>
    <span class="sh-top-logo-sub">Early Warning Platform</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    nav_cols = st.columns([1, 1, 1, 1.45], gap="small")
    links = [
        ("views/home.py", "Home"),
        ("views/risk_map.py", "Risk Map"),
        ("views/insights.py", "Insights"),
        ("views/about.py", "Method & Data"),
    ]
    for column, (page, label) in zip(nav_cols, links):
        is_active = (label == norm_active)
        btn_label = f"●  {label}" if is_active else label
        with column:
            if st.button(
                btn_label,
                key=f"nav_{label}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.switch_page(page)


def render_hero_banner() -> str:
    hero_bg = get_hero_background_css()
    return f"""
<div class="sh-hero-banner" style="background: linear-gradient(90deg, rgba(15, 23, 42, 0.85) 0%, rgba(15, 23, 42, 0.4) 65%, rgba(15, 23, 42, 0.2) 100%), {hero_bg} center/cover no-repeat;">
  <div class="sh-hero-content">
                <div class="sh-hero-title">Hyperlocal Flash-Flood Early Warning</div>
                <div class="sh-hero-sub">Kamrup Metropolitan, Assam</div>
                <div class="sh-hero-desc">SHAILA combines weather-trigger modelling with terrain susceptibility and official vulnerability data to surface cell-level risk for operational review.</div>
    <div class="sh-hero-actions">
      <a href="/risk_map" target="_self" class="sh-btn-primary">
                        <span>Open Risk Map</span>
      </a>
      <a href="/about" target="_self" class="sh-btn-secondary">
                        <span>Explore Methodology</span>
      </a>
    </div>
  </div>
</div>
"""


def render_feature_pills() -> str:
    return f"""
<div class="sh-capability-grid">
    <div class="sh-capability">
        <div class="sh-capability-icon">◒</div>
    <div>
            <div class="sh-capability-title">Weather &amp; Soil Monitoring</div>
            <div class="sh-capability-text">Rainfall, soil moisture and temperature features drive the dynamic trigger layer.</div>
    </div>
  </div>
    <div class="sh-capability">
        <div class="sh-capability-icon">⌁</div>
    <div>
            <div class="sh-capability-title">Terrain Susceptibility</div>
            <div class="sh-capability-text">Slope-derived vulnerability is combined with official hazard floors and incident evidence.</div>
    </div>
  </div>
    <div class="sh-capability">
        <div class="sh-capability-icon">◇</div>
    <div>
            <div class="sh-capability-title">Satellite / ERA5 Data</div>
            <div class="sh-capability-text">ERA5-derived weather inputs and local terrain rasters support the 1 km grid.</div>
    </div>
  </div>
    <div class="sh-capability">
        <div class="sh-capability-icon">✦</div>
    <div>
            <div class="sh-capability-title">ML Risk Assessment</div>
            <div class="sh-capability-text">A balanced Random Forest estimates weather-trigger probability for mapped cells.</div>
    </div>
  </div>
</div>
"""


def render_kpi_cards(peak_risk_pct: float = 78.5, rainfall_mm: float = 92.0, active_cells: int = 904) -> str:
    if peak_risk_pct >= 75:
        risk_class = "risk-severe"
        risk_title = "HIGH RISK"
        risk_sub = "Severe Threat"
        risk_icon = "⚠️"
    elif peak_risk_pct >= 50:
        risk_class = "risk-high"
        risk_title = "MODERATE RISK"
        risk_sub = "Elevated Threat"
        risk_icon = "⚡"
    elif peak_risk_pct >= 25:
        risk_class = "risk-moderate"
        risk_title = "MEDIUM RISK"
        risk_sub = "Advisory"
        risk_icon = "🌧️"
    else:
        risk_class = "risk-low"
        risk_title = "LOW RISK"
        risk_sub = "Normal Condition"
        risk_icon = "✅"

    return f"""
<div class="sh-kpi-grid">
  <div class="sh-kpi-card {risk_class}">
    <div class="sh-kpi-header">Risk Level</div>
    <div class="sh-kpi-body">
      <div style="font-size: 2rem;">{risk_icon}</div>
      <div>
        <div class="sh-kpi-val">{risk_title}</div>
        <div class="sh-kpi-sub">{risk_sub} ({peak_risk_pct:.1f}%)</div>
      </div>
    </div>
  </div>
  <div class="sh-kpi-card blue-metric">
    <div class="sh-kpi-header">Rainfall (Antecedent / 24h)</div>
    <div class="sh-kpi-body">
      <div style="font-size: 2rem;">🌧️</div>
      <div>
        <div class="sh-kpi-val">{rainfall_mm:.1f} mm</div>
        <div class="sh-kpi-sub">Precipitation Index</div>
      </div>
    </div>
  </div>
  <div class="sh-kpi-card blue-metric">
    <div class="sh-kpi-header">Grid Status</div>
    <div class="sh-kpi-body">
      <div style="font-size: 2rem;">🌊</div>
      <div>
        <div class="sh-kpi-val">{active_cells:,} Cells</div>
        <div class="sh-kpi-sub">Monitoring Active</div>
      </div>
    </div>
  </div>
</div>
"""


def render_key_features_badges() -> str:
    return f"""
<div class="sh-badges-grid">
  <div class="sh-badge-circle-item">
    <div class="sh-circle-icon">⚙️</div>
    <div class="sh-circle-title">AI-Powered Analytics</div>
    <div class="sh-circle-desc">Machine Learning Predictions</div>
  </div>
  <div class="sh-badge-circle-item">
    <div class="sh-circle-icon">💧</div>
    <div class="sh-circle-title">Hydrological Modelling</div>
    <div class="sh-circle-desc">Antecedent Precipitation & Soil</div>
  </div>
  <div class="sh-badge-circle-item">
    <div class="sh-circle-icon">🛰️</div>
    <div class="sh-circle-title">Satellite Monitoring</div>
    <div class="sh-circle-desc">1 km SRTM/CartoDEM Integration</div>
  </div>
  <div class="sh-badge-circle-item">
    <div class="sh-circle-icon">🚨</div>
    <div class="sh-circle-title">Instant Alerts</div>
    <div class="sh-circle-desc">Cell-level Early Warning Notifications</div>
  </div>
</div>
"""


def render_subscribe_card() -> str:
    return f"""
<div class="sh-subscribe-card">
  <div class="sh-sub-title">Stay Updated on Flood Alerts</div>
  <div class="sh-sub-desc">Subscribe for Latest Updates & Safety Alerts in Kamrup Metropolitan</div>
  <div class="sh-sub-form">
    <input type="email" class="sh-sub-input" placeholder="Enter your email address" />
    <button class="sh-sub-btn" type="button">Subscribe Now</button>
  </div>
</div>
"""


def render_footer() -> str:
    return f"""
<div class="sh-footer">
  <div>
        <b style="color:#FFF;">SHAILA</b> &middot; Hyperlocal early-warning decision support for Kamrup Metropolitan
  </div>
  <div class="sh-footer-links">
    <a href="/">Quick Links</a>
    <a href="/about">Privacy Policy</a>
    <a href="/about">Terms of Service</a>
    <a href="/about">Contact Us</a>
  </div>
</div>
"""


