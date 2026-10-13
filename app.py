from __future__ import annotations

import base64
import csv
import hashlib
import html
import io
import json
import os
import time
from typing import Any
from urllib.parse import urljoin

import requests
import streamlit as st
from PIL import Image, ImageStat, UnidentifiedImageError

# ============================================================
# AGRISCAN AI — STREAMLIT EDITION
# High-contrast forest/sage design, animated UI, leaf classifier,
# optional Gemini multimodal second opinion, and ESP32-CAM adapter.
# ============================================================

MODEL_OPTIONS = {
    "Specialist leaf classifier · Vision Transformer": "kimcomehome/plantvillage-vit-leaf-disease",
    "Lightweight fallback · MobileNetV2": "Kathir56/plant-disease-tamilnadu",
}
CUSTOM_MODEL_ID = os.getenv("AGRISCAN_MODEL_ID", "").strip()
if CUSTOM_MODEL_ID and CUSTOM_MODEL_ID not in MODEL_OPTIONS.values():
    MODEL_OPTIONS["Custom model · AGRISCAN_MODEL_ID"] = CUSTOM_MODEL_ID

DEFAULT_GEMINI_MODEL = os.getenv("AGRISCAN_GEMINI_MODEL", "gemini-3.1-pro-preview").strip()
MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
PROJECT_CREDIT = "Jayakanth & Project Partner"  # Replace with your teammate's name when known.

st.set_page_config(
    page_title="Agriscan AI | Plant Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def get_secret(name: str, default: str = "") -> str:
    """Read credentials on the server only. Never save secrets in browser state."""
    value = os.getenv(name, "")
    if value:
        return value.strip()
    try:
        value = st.secrets.get(name, default)
        return str(value).strip() if value is not None else default
    except Exception:
        return default


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GEMINI_MODEL = get_secret("AGRISCAN_GEMINI_MODEL", DEFAULT_GEMINI_MODEL) or DEFAULT_GEMINI_MODEL

# -------------------- Design system + animations --------------------
st.markdown(
    r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {
  --ag-bg:#07110c; --ag-bg2:#0a1810; --ag-card:#12251a; --ag-card2:#193523;
  --ag-sage:#c9e8b7; --ag-mint:#dff4d1; --ag-text:#f4f8f0; --ag-body:#e0eadc;
  --ag-muted:#bfd0ba; --ag-line:#49664d; --ag-deep:#102719; --ag-gold:#f1d99a;
}
html, body, [class*="css"] { font-family:'DM Sans',ui-sans-serif,system-ui,sans-serif; }
.stApp {
  background:linear-gradient(140deg,#06100b 0%,#0a1910 47%,#07120c 100%) !important;
  color:var(--ag-text) !important; font-size:16px;
}
.stApp::before {
  content:""; position:fixed; inset:-25%; z-index:0; pointer-events:none;
  background:radial-gradient(ellipse at 18% 18%,rgba(104,159,76,.18),transparent 30%),
             radial-gradient(ellipse at 81% 28%,rgba(67,144,89,.13),transparent 28%),
             radial-gradient(ellipse at 60% 90%,rgba(145,183,99,.08),transparent 30%);
  animation:ambient-drift 22s ease-in-out infinite alternate;
}
.block-container { max-width:1320px; padding:1rem 2rem 3rem; position:relative; z-index:1; }
[data-testid="stHeader"] { background:rgba(7,17,12,.78) !important; backdrop-filter:blur(18px); }
[data-testid="stToolbar"] { right:1rem; }
#MainMenu, footer { visibility:hidden; }

/* Readability baseline. Avoid applying text colors blindly inside buttons. */
.stApp p, .stApp li, .stApp label, .stMarkdown, .stMarkdown p, .stMarkdown li,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
  color:var(--ag-body) !important;
}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6,
[data-testid="stMarkdownContainer"] h1,[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,[data-testid="stMarkdownContainer"] h4 {
  color:var(--ag-text) !important; font-family:'Manrope','DM Sans',sans-serif !important;
  letter-spacing:-.035em;
}
.stCaption,[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p {
  color:#c5d6c0 !important; font-size:.9rem !important; line-height:1.6 !important;
}

/* Navigation */
.ag-nav { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.5rem 0 1.2rem; border-bottom:1px solid rgba(190,225,177,.17); margin-bottom:1.35rem; }
.ag-brand { display:flex; align-items:center; gap:.7rem; color:#edf7e6; font-family:'Manrope',sans-serif; font-size:1.2rem; font-weight:800; letter-spacing:-.04em; }
.ag-brand-mark { width:42px; height:42px; display:grid; place-items:center; border:1px solid rgba(221,245,204,.5); border-radius:15px; background:linear-gradient(145deg,#d9f0c7,#8cbd80); color:#0d2817; box-shadow:0 0 24px rgba(145,198,124,.2); animation:leaf-breathe 4.5s ease-in-out infinite; }
.ag-nav-right { color:#c0d4ba; font-size:.83rem; text-align:right; letter-spacing:.08em; }
.ag-status-dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:#dfbf78; margin-right:.4rem; box-shadow:0 0 0 4px rgba(223,191,120,.12); }

/* Hero */
.ag-hero { position:relative; overflow:hidden; isolation:isolate; padding:clamp(1.7rem,4vw,3.15rem); border-radius:29px; border:1px solid rgba(195,229,179,.34); background:radial-gradient(ellipse at 78% 10%,rgba(141,197,103,.23),transparent 34%),linear-gradient(115deg,rgba(27,57,36,.98),rgba(10,29,18,.98)); box-shadow:0 28px 70px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.07); margin-bottom:1.7rem; animation:reveal-up .7s cubic-bezier(.2,.8,.2,1) both; }
.ag-hero:before { content:""; position:absolute; z-index:-1; width:280px; height:280px; border:1px solid rgba(210,238,194,.13); border-radius:50%; right:7%; top:-110px; box-shadow:0 0 0 25px rgba(210,238,194,.025),0 0 0 54px rgba(210,238,194,.02); animation:orbit-slow 36s linear infinite; }
.ag-hero:after { content:"✳"; position:absolute; right:8%; bottom:-7.3rem; font-size:18rem; line-height:1; color:rgba(214,240,198,.045); pointer-events:none; animation:hero-float 7s ease-in-out infinite; }
.ag-eyebrow { position:relative; z-index:1; text-transform:uppercase; letter-spacing:2.8px; font-size:.8rem; font-weight:800; color:#d4edc6; margin-bottom:1rem; }
.ag-hero h1 { position:relative; z-index:1; font-family:'Manrope',sans-serif; font-size:clamp(2.6rem,5.2vw,4.5rem); line-height:1.04; color:#f5f9f1 !important; font-weight:800; letter-spacing:-.065em; margin:0 0 .9rem; }
.ag-hero p { position:relative; z-index:1; max-width:730px; color:#e0ebdc !important; font-size:1.1rem; line-height:1.8; margin:0; }
.ag-hero-tag { position:relative; z-index:1; display:inline-flex; margin-top:1.35rem; padding:.6rem .95rem; border:1px solid rgba(213,240,197,.35); background:rgba(213,240,197,.1); border-radius:999px; color:#e1f5d4; font-size:.88rem; font-weight:700; }
.ag-floating-leaf { position:absolute; z-index:1; right:13%; top:23%; font-size:5rem; filter:drop-shadow(0 8px 24px rgba(163,216,126,.18)); animation:leaf-float 6s ease-in-out infinite; }

/* Component surfaces and layout */
.ag-section-head { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin:.7rem 0 1rem; }
.ag-section-title { color:#f2f7ee; font-family:'Manrope',sans-serif; font-size:1.7rem; line-height:1.28; font-weight:800; letter-spacing:-.04em; }
.ag-section-sub { color:#d0dfcb; font-size:1rem; line-height:1.75; margin-top:.35rem; margin-bottom:1.15rem; }
.ag-kicker { color:#c8e8b7; text-transform:uppercase; letter-spacing:1.7px; font-size:.78rem; font-weight:800; }
.ag-glass { background:linear-gradient(145deg,rgba(27,52,35,.96),rgba(13,29,19,.98)); border:1px solid rgba(188,224,174,.27); border-radius:22px; padding:1.35rem; box-shadow:0 15px 38px rgba(0,0,0,.18),inset 0 1px 0 rgba(255,255,255,.045); transition:transform .24s ease,border-color .24s ease,box-shadow .24s ease; animation:reveal-up .55s cubic-bezier(.2,.8,.2,1) both; }
.ag-glass:hover { transform:translateY(-3px); border-color:rgba(203,237,187,.48); box-shadow:0 22px 48px rgba(0,0,0,.23),0 0 24px rgba(131,183,104,.06); }
.ag-glass-title { color:#f3f8ef; font-family:'Manrope',sans-serif; font-weight:800; font-size:1.08rem; line-height:1.45; margin-bottom:.75rem; }
.ag-secondary { color:#d1dfcc; font-size:.98rem; line-height:1.8; }
.ag-muted { color:#bdd0b8; font-size:.9rem; line-height:1.7; }
.ag-pill { display:inline-flex; align-items:center; gap:.35rem; padding:.4rem .7rem; border:1px solid rgba(197,230,181,.3); border-radius:999px; background:rgba(178,220,158,.1); color:#e0f2d4; font-size:.82rem; font-weight:800; }
.ag-stat { background:linear-gradient(145deg,rgba(23,46,29,.97),rgba(13,29,19,.97)); border:1px solid rgba(186,223,171,.25); border-radius:18px; padding:1.1rem 1.2rem; min-height:106px; }
.ag-stat-label { color:#c3d8bd; font-size:.78rem; font-weight:800; letter-spacing:1.2px; text-transform:uppercase; }
.ag-stat-value { color:#f2f8ed; font:800 1.25rem 'Manrope',sans-serif; margin-top:.45rem; overflow-wrap:anywhere; }
.ag-stat-note { color:#c3d7bd; font-size:.86rem; margin-top:.25rem; line-height:1.5; }
.ag-report-card { border:1px solid rgba(190,224,176,.29); background:linear-gradient(145deg,rgba(30,58,38,.98),rgba(13,31,20,.99)); padding:1.5rem; border-radius:22px; height:100%; animation:reveal-up .5s ease both; }
.ag-result-name { color:#f7faf4; font-family:'Manrope',sans-serif; font-size:clamp(1.2rem,2.3vw,1.8rem); line-height:1.42; font-weight:800; overflow-wrap:anywhere; margin-top:.6rem; }
.ag-score-value { color:#e0f4d2; font-family:'Manrope',sans-serif; font-size:clamp(2.5rem,4.5vw,3.5rem); font-weight:800; letter-spacing:-.055em; line-height:1.2; margin:.3rem 0 .2rem; }
.ag-track { height:10px; width:100%; border-radius:999px; background:#263c2b; margin-top:.7rem; overflow:hidden; }
.ag-fill { height:100%; border-radius:999px; background:linear-gradient(90deg,#78ad6e,#cdebb5,#f0f9df); background-size:200% 100%; animation:progress-sheen 3.4s linear infinite; }
.ag-candidate { display:flex; align-items:center; justify-content:space-between; gap:1rem; border:1px solid rgba(187,220,172,.2); border-radius:15px; background:rgba(20,40,26,.91); padding:.95rem 1rem; margin:.6rem 0; transition:transform .18s ease,border-color .18s ease; }
.ag-candidate:hover { transform:translateX(3px); border-color:rgba(194,231,176,.42); }
.ag-candidate-name { color:#f0f6ec; font-size:1rem; line-height:1.5; font-weight:650; overflow-wrap:anywhere; }
.ag-candidate-score { color:#e1f3d5; font-size:1rem; font-weight:800; white-space:nowrap; }
.ag-step-num { display:grid; place-items:center; width:42px; height:42px; border-radius:14px; background:linear-gradient(140deg,#d8f0c6,#8abb7b); color:#102719; font-weight:900; margin-bottom:.9rem; box-shadow:0 7px 18px rgba(144,196,124,.12); }
.ag-step-title { color:#f4f8ef; font-weight:800; font-size:1.05rem; margin-bottom:.4rem; }
.ag-step-body { color:#d0dfca; font-size:.96rem; line-height:1.75; }
.ag-footer { padding:1.8rem 0 .3rem; text-align:center; color:#bdcfb8; font-size:.88rem; line-height:1.9; }
.ag-footer strong { color:#d5edc5; letter-spacing:1.1px; }
.ag-divider { height:1px; margin:1.5rem 0; background:linear-gradient(90deg,transparent,rgba(196,227,179,.3),transparent); }

/* widget labels, selectable cards, inputs and upload area */
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
[data-testid="stRadio"] label, [data-testid="stCheckbox"] label,
[data-testid="stTextInput"] label, [data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label, [data-testid="stFileUploader"] label {
  color:#e6f0e1 !important; font-size:1rem !important; font-weight:650 !important;
}
div[role="radiogroup"] { gap:.55rem; }
div[role="radiogroup"] label { border:1px solid rgba(190,222,176,.26); border-radius:14px; padding:.7rem .95rem; background:rgba(18,37,24,.96); }
div[role="radiogroup"] label p,div[role="radiogroup"] label span { color:#edf5e8 !important; font-size:.96rem !important; font-weight:750 !important; }
div[role="radiogroup"] label:has(input:checked) { border-color:#c1e5ad; background:rgba(137,184,118,.24); box-shadow:inset 0 0 0 1px rgba(193,229,173,.12); }
.stTextInput input,.stNumberInput input,.stSelectbox [data-baseweb="select"] > div,.stTextArea textarea {
  background:#0e2115 !important; color:#f5f8f2 !important; border-color:#5b795b !important; border-radius:13px !important; font-size:1rem !important;
}
.stTextInput input::placeholder,.stTextArea textarea::placeholder { color:#b8cbb3 !important; }
[data-baseweb="popover"],[data-baseweb="menu"] { background:#14281a !important; }
[role="option"] { color:#f4f8f0 !important; }
/* Real Streamlit bordered containers own their child widgets. This avoids invalid
   open/close HTML wrappers that can cause misaligned controls across reruns. */
[data-testid="stVerticalBlockBorderWrapper"] {
  background:linear-gradient(145deg,rgba(23,46,30,.96),rgba(12,27,17,.99)) !important;
  border:1px solid rgba(188,224,174,.3) !important;
  border-radius:22px !important;
  padding:1.05rem !important;
  box-shadow:0 14px 35px rgba(0,0,0,.14),inset 0 1px 0 rgba(255,255,255,.035);
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] { gap:.8rem; }
[data-testid="stFileUploader"] { background:rgba(9,23,14,.92); border:1px dashed rgba(194,230,175,.62); border-radius:19px; padding:.65rem; }
[data-testid="stFileUploaderDropzone"] { background:#13291a !important; border:1px dashed #587b55 !important; border-radius:15px !important; }
[data-testid="stFileUploaderDropzone"] p,[data-testid="stFileUploaderDropzone"] span { color:#f0f6ec !important; font-size:.95rem !important; }
[data-testid="stFileUploaderDropzone"] button { background:#d9f0cb !important; color:#0e2917 !important; -webkit-text-fill-color:#0e2917 !important; border:1px solid #d9f0cb !important; border-radius:11px !important; font-weight:850 !important; }
[data-testid="stCameraInput"] { border-radius:17px; overflow:hidden; }

/* BUTTON TEXT FIX: outer button AND nested markdown p/span labels are styled. */
div[data-testid="stButton"] > button, .stApp button[data-testid^="stBaseButton"] {
  min-height:3.15rem; padding:.65rem 1.15rem; border:1px solid #526f53 !important; border-radius:14px !important;
  background:#193523 !important; color:#f3f8ef !important; -webkit-text-fill-color:#f3f8ef !important;
  font-family:'DM Sans',sans-serif !important; font-size:1rem !important; font-weight:850 !important;
  box-shadow:0 6px 17px rgba(0,0,0,.13); transition:transform .18s ease,box-shadow .22s ease,border-color .22s ease,background .22s ease;
}
div[data-testid="stButton"] > button:hover,.stApp button[data-testid^="stBaseButton"]:hover { background:#2b5034 !important; color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; border-color:#c7e7b4 !important; transform:translateY(-2px); box-shadow:0 10px 26px rgba(0,0,0,.22),0 0 18px rgba(157,208,132,.12); }
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stButton"] > button[data-testid="stBaseButton-primary"],
.stApp button[kind="primary"],.stApp button[data-testid="stBaseButton-primary"] {
  background:linear-gradient(120deg,#d9f0cb 0%,#b6dfa3 45%,#d8efc6 100%) !important;
  background-size:180% 100% !important; color:#102719 !important; -webkit-text-fill-color:#102719 !important;
  border:1px solid #e1f5d3 !important; box-shadow:0 9px 28px rgba(125,181,105,.19); animation:button-glow 5s ease-in-out infinite;
}
div[data-testid="stButton"] > button[kind="primary"] *,
div[data-testid="stButton"] > button[data-testid="stBaseButton-primary"] *,
.stApp button[kind="primary"] *, .stApp button[data-testid="stBaseButton-primary"] *,
.stApp button[kind="primary"] p,.stApp button[kind="primary"] span,
.stApp button[data-testid="stBaseButton-primary"] p,.stApp button[data-testid="stBaseButton-primary"] span,
.stApp button[kind="primary"] div[data-testid="stMarkdownContainer"] p {
  color:#102719 !important; -webkit-text-fill-color:#102719 !important; opacity:1 !important; text-shadow:none !important; font-weight:850 !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover *,
.stApp button[data-testid="stBaseButton-primary"]:hover * { color:#081c0e !important; -webkit-text-fill-color:#081c0e !important; }
div[data-testid="stButton"] > button:disabled,.stApp button[data-testid^="stBaseButton"]:disabled { background:#263b2a !important; color:#d0dccb !important; -webkit-text-fill-color:#d0dccb !important; border-color:#52664f !important; animation:none !important; transform:none !important; }

/* Tabs + progress + alert + metric */
.stTabs [data-baseweb="tab-list"] { background:#0a1a10; border:1px solid rgba(190,222,176,.25); border-radius:16px; padding:5px; gap:5px; }
.stTabs [data-baseweb="tab"] { border-radius:12px; padding:.75rem 1rem; color:#e0ebda !important; }
.stTabs [data-baseweb="tab"] p { color:inherit !important; font-size:.98rem !important; font-weight:800 !important; }
.stTabs [aria-selected="true"] { background:rgba(141,188,122,.26) !important; border:1px solid rgba(204,235,189,.42) !important; }
.stTabs [data-baseweb="tab-highlight"] { background:#c8e7b7 !important; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#193523,#102217) !important; border:1px solid rgba(190,222,176,.3) !important; border-radius:17px !important; padding:1.15rem !important; }
[data-testid="stMetric"] label,[data-testid="stMetricLabel"],[data-testid="stMetricValue"],[data-testid="stMetricDelta"] { color:#f3f8ef !important; }
[data-testid="stAlert"] { border-radius:15px !important; border-width:1px !important; }
[data-testid="stExpander"] { border:1px solid rgba(183,220,166,.28) !important; border-radius:16px !important; background:#102318 !important; }
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary p { color:#f0f6eb !important; font-weight:750 !important; font-size:1rem !important; }
.stProgress > div > div > div > div { background:linear-gradient(90deg,#79b46f,#d3edbc,#8fc47c) !important; background-size:200% 100%; animation:progress-sheen 2s linear infinite; }
[data-testid="stSpinner"] p { color:#e7f2e2 !important; font-size:1rem !important; }
hr { border-color:rgba(183,220,166,.19) !important; margin:1.8rem 0 !important; }
:focus-visible { outline:3px solid #d2efc0 !important; outline-offset:3px !important; }

/* Editorial redesign: one clear visual focal point, quieter supporting cards. */
.block-container { max-width:1240px; padding:1.2rem 2rem 3.5rem; }
.ag-nav { padding:.65rem 0 1.35rem; margin-bottom:1.7rem; }
.ag-brand-mark { width:45px; height:45px; border-radius:16px; }
.ag-hero-layout { display:grid; grid-template-columns:minmax(0,1.18fr) minmax(290px,.82fr); gap:1.4rem; align-items:stretch; margin-bottom:1.8rem; }
.ag-hero { min-height:350px; display:flex; flex-direction:column; justify-content:center; margin-bottom:0; }
.ag-hero h1 { max-width:730px; font-size:clamp(2.8rem,5.7vw,5.1rem); line-height:1.01; }
.ag-hero h1 span { color:#c8e8b7; }
.ag-hero p { max-width:630px; font-size:1.06rem; }
.ag-hero-tag { margin-top:1.5rem; }
.ag-hero-visual { position:relative; isolation:isolate; min-height:350px; overflow:hidden; border-radius:29px; border:1px solid rgba(195,229,179,.28); background:radial-gradient(circle at 52% 40%,rgba(135,190,104,.24),transparent 42%),linear-gradient(145deg,rgba(26,52,34,.96),rgba(8,24,14,.99)); box-shadow:0 25px 65px rgba(0,0,0,.23),inset 0 1px 0 rgba(255,255,255,.07); display:flex; align-items:center; justify-content:center; }
.ag-hero-visual:before { content:""; position:absolute; width:235px; height:235px; border-radius:50%; border:1px solid rgba(211,238,195,.26); box-shadow:0 0 0 17px rgba(195,229,179,.035),0 0 0 42px rgba(195,229,179,.025),0 0 0 67px rgba(195,229,179,.018); animation:orbit-slow 48s linear infinite; }
.ag-orbit { position:absolute; width:190px; height:190px; border-radius:50%; border:1px dashed rgba(203,235,187,.34); animation:orbit-slow 29s linear infinite reverse; }
.ag-orbit:before { content:""; position:absolute; top:17px; right:20px; width:10px; height:10px; border-radius:50%; background:#d8f0c6; box-shadow:0 0 16px rgba(216,240,198,.8); }
.ag-hero-leaf { z-index:1; font-size:6.3rem; filter:drop-shadow(0 12px 35px rgba(146,205,117,.3)); animation:hero-float 6s ease-in-out infinite; }
.ag-visual-label { position:absolute; z-index:2; top:1.2rem; left:1.2rem; color:#cce6c1; font-size:.76rem; letter-spacing:1.9px; text-transform:uppercase; font-weight:850; }
.ag-visual-status { position:absolute; z-index:2; bottom:1.2rem; left:1.2rem; right:1.2rem; padding:1rem 1.1rem; border:1px solid rgba(192,227,177,.29); background:rgba(8,24,14,.76); backdrop-filter:blur(18px); border-radius:18px; display:flex; align-items:center; justify-content:space-between; gap:1rem; }
.ag-visual-status strong { color:#f0f7ea; font-size:1rem; display:block; }
.ag-visual-status span { color:#c5d9bf; font-size:.84rem; display:block; margin-top:.25rem; }
.ag-live-dot { width:9px; height:9px; display:inline-block; flex:0 0 9px; border-radius:50%; background:#badf9e; box-shadow:0 0 0 5px rgba(186,223,158,.12); animation:dot-pulse 2.5s ease-in-out infinite; }
.ag-stat { min-height:112px; transition:transform .22s ease,border-color .22s ease; }
.ag-stat:hover { transform:translateY(-3px); border-color:rgba(207,236,190,.5); }
.ag-section-head { margin-top:1.2rem; margin-bottom:1.2rem; }
.ag-section-title { font-size:clamp(1.55rem,2.4vw,2rem); }
.ag-section-sub { max-width:780px; font-size:1.01rem; }
.ag-glass { padding:1.5rem; border-radius:24px; }
.ag-report-card { border-radius:24px; padding:1.7rem; }
.ag-candidate { padding:1rem 1.1rem; }
.ag-step-num { border-radius:50%; }
.ag-feature-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; }
.ag-feature-card { min-height:185px; position:relative; overflow:hidden; border-radius:22px; padding:1.35rem; background:linear-gradient(145deg,rgba(24,48,31,.93),rgba(12,27,17,.97)); border:1px solid rgba(188,224,174,.23); box-shadow:0 15px 38px rgba(0,0,0,.13); transition:transform .25s ease,border-color .25s ease; animation:reveal-up .6s both; }
.ag-feature-card:hover { transform:translateY(-4px); border-color:rgba(203,237,187,.5); }
.ag-feature-card:nth-child(2) { animation-delay:.08s; }
.ag-feature-card:nth-child(3) { animation-delay:.16s; }
.ag-feature-icon { width:47px; height:47px; border-radius:15px; display:grid; place-items:center; background:linear-gradient(145deg,#d9f0c7,#8cbd80); color:#0d2817; font-size:1.35rem; margin-bottom:1rem; box-shadow:0 7px 20px rgba(143,191,125,.13); }
.ag-feature-title { color:#f3f8ef; font-family:'Manrope',sans-serif; font-size:1.05rem; font-weight:800; margin-bottom:.4rem; }
.ag-feature-body { color:#d0dfca; font-size:.95rem; line-height:1.7; }
.ag-quality-score { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:.35rem; }
.ag-quality-title { color:#f4f8ef; font-weight:800; font-size:1rem; }
.ag-quality-badge { padding:.35rem .65rem; border-radius:999px; background:rgba(188,224,174,.13); border:1px solid rgba(188,224,174,.28); color:#e0f2d4; font-weight:800; font-size:.8rem; }
.ag-quality-track { height:8px; background:#263d2a; border-radius:99px; overflow:hidden; margin:.8rem 0; }
.ag-quality-fill { height:100%; background:linear-gradient(90deg,#7bad6e,#d6f0bd); border-radius:99px; }
.ag-history-row { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:1rem; align-items:center; padding:1rem 0; border-bottom:1px solid rgba(188,224,174,.15); }
.ag-history-row:last-child { border-bottom:0; }
.ag-history-name { color:#f1f7ec; font-weight:800; line-height:1.45; overflow-wrap:anywhere; }
.ag-history-meta { color:#c0d3ba; font-size:.88rem; line-height:1.7; margin-top:.25rem; }
.ag-history-score { color:#dbf1cb; font-family:'Manrope',sans-serif; font-size:1.2rem; font-weight:850; text-align:right; }
.ag-feature-note { color:#bed2b8; font-size:.87rem; line-height:1.7; }
@keyframes dot-pulse { 0%,100% { box-shadow:0 0 0 4px rgba(186,223,158,.11); } 50% { box-shadow:0 0 0 8px rgba(186,223,158,.025); } }
@keyframes reveal-up { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
@keyframes ambient-drift { from { transform:translate3d(-1.2%,0,0) scale(1); } to { transform:translate3d(1.2%,1%,0) scale(1.035); } }
@keyframes hero-float { 0%,100% { transform:translateY(0) rotate(-4deg); } 50% { transform:translateY(-12px) rotate(4deg); } }
@keyframes leaf-float { 0%,100% { transform:translateY(0) rotate(-7deg); } 50% { transform:translateY(-10px) rotate(6deg); } }
@keyframes orbit-slow { from { transform:rotate(0deg); } to { transform:rotate(360deg); } }
@keyframes leaf-breathe { 0%,100% { transform:translateY(0); box-shadow:0 5px 20px rgba(144,196,124,.17); } 50% { transform:translateY(-2px); box-shadow:0 8px 28px rgba(144,196,124,.3); } }
@keyframes button-glow { 0%,100% { background-position:0% 50%; box-shadow:0 8px 22px rgba(125,181,105,.14); } 50% { background-position:100% 50%; box-shadow:0 10px 30px rgba(125,181,105,.25); } }
@keyframes progress-sheen { from { background-position:0% 50%; } to { background-position:200% 50%; } }
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; scroll-behavior:auto !important; } }
@media (max-width:900px) {
  .ag-hero-layout { grid-template-columns:1fr; }
  .ag-hero-visual { min-height:280px; }
  .ag-feature-grid { grid-template-columns:1fr; }
}
@media (max-width:760px) {
  .block-container { padding:.9rem 1rem 2rem; }
  .ag-hero { min-height:unset; }
  .ag-nav { align-items:flex-start; flex-direction:column; }
  .ag-nav-right { text-align:left; font-size:.78rem; }
  .ag-hero { padding:1.65rem 1.35rem; border-radius:22px; }
  .ag-hero h1 { font-size:2.5rem; }
  .ag-hero:after { right:-16%; top:8%; font-size:10rem; }
  .ag-floating-leaf { display:none; }
  .ag-section-title { font-size:1.45rem; }
  .ag-candidate { align-items:flex-start; }
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------- Secrets / state ----------------------------
def init_state() -> None:
    defaults = {
        "ag_report": None,
        "ag_image_bytes": None,
        "ag_image_source": None,
        "ag_image_name": None,
        "ag_image_hash": None,
        "ag_last_camera_auto_hash": None,
        "ag_device_status": None,
        "ag_device_error": None,
        "ag_last_capture_time": None,
        "ag_esp32_capture_bytes": None,
        "ag_esp32_capture_name": None,
        "ag_esp32_pending_autoscan": False,
        "ag_history": [],
        "ag_field_note": "",
        "ag_comparison": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource(show_spinner=False)
def get_classifier(model_id: str):
    from transformers import pipeline

    return pipeline("image-classification", model=model_id, device=-1)


def pretty_label(label: str) -> str:
    return str(label).replace("___", " — ").replace("_", " ").strip()


def escaped(value: Any) -> str:
    return html.escape(str(value))


def mime_from_format(fmt: str) -> str:
    return {"JPEG": "image/jpeg", "JPG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}.get(fmt.upper(), "image/jpeg")


def validate_image(raw: bytes) -> tuple[Image.Image, str, tuple[int, int]]:
    if not raw:
        raise ValueError("The image file is empty.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("This image is over 10 MB. Resize it or choose a smaller image.")
    try:
        with Image.open(io.BytesIO(raw)) as check:
            check.verify()
        with Image.open(io.BytesIO(raw)) as opened:
            fmt = opened.format or "Unknown"
            image = opened.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("That file is not a valid JPG, PNG or WebP image. Choose another photo.") from exc
    if image.width < 96 or image.height < 96:
        raise ValueError("This image is very small. Please use a clearer image at least 96 × 96 pixels.")
    return image, fmt, image.size


def assess_capture_quality(image: Image.Image) -> dict[str, Any]:
    """Transparent, lightweight image-quality hints; never a disease prediction."""
    gray = image.convert("L")
    stats = ImageStat.Stat(gray)
    brightness = float(stats.mean[0])
    contrast = float(stats.stddev[0])
    width, height = image.size
    score = 100
    notes: list[str] = []

    if min(width, height) < 320:
        score -= 20
        notes.append("Low image resolution may hide small visual details.")
    if brightness < 48:
        score -= 25
        notes.append("The image looks quite dark; try softer, brighter natural light.")
    elif brightness < 72:
        score -= 10
        notes.append("The image is somewhat dark; more even light may help.")
    elif brightness > 224:
        score -= 25
        notes.append("The image is very bright; reduce glare or direct sunlight.")
    elif brightness > 205:
        score -= 10
        notes.append("Bright areas may wash out leaf details.")
    if contrast < 18:
        score -= 20
        notes.append("The image has low tonal contrast; choose a clearer angle/background.")
    score = max(0, min(100, score))
    if not notes:
        notes.append("Basic lighting, contrast and resolution checks look reasonable.")
    label = "Looks good" if score >= 80 else ("Could be improved" if score >= 55 else "Consider a rescan")
    return {
        "score": score,
        "label": label,
        "brightness": round(brightness, 1),
        "contrast": round(contrast, 1),
        "width": width,
        "height": height,
        "notes": notes,
    }


def clear_active_image() -> None:
    for key in (
        "ag_image_bytes", "ag_image_source", "ag_image_name", "ag_image_hash", "ag_report",
        "ag_esp32_capture_bytes", "ag_esp32_capture_name", "ag_esp32_pending_autoscan",
        "ag_last_camera_auto_hash", "ag_upload_widget", "ag_camera_widget",
    ):
        if key in st.session_state:
            st.session_state[key] = None


def set_active_image(raw: bytes, source: str, filename: str) -> tuple[str, Image.Image, str]:
    image, fmt, _ = validate_image(raw)
    digest = hashlib.sha256(raw).hexdigest()
    if st.session_state.get("ag_image_hash") != digest:
        st.session_state["ag_report"] = None
    st.session_state["ag_image_bytes"] = raw
    st.session_state["ag_image_source"] = source
    st.session_state["ag_image_name"] = filename
    st.session_state["ag_image_hash"] = digest
    return digest, image, mime_from_format(fmt)


# ---------------------------- Model engines ----------------------------
def normalize_classifier_results(raw_results: Any) -> list[dict[str, Any]]:
    clean: list[dict[str, Any]] = []
    if not isinstance(raw_results, list):
        return clean
    for item in raw_results:
        if not isinstance(item, dict) or not item.get("label"):
            continue
        try:
            score = float(item.get("score"))
        except (TypeError, ValueError):
            continue
        if not 0 <= score <= 1:
            continue
        clean.append({"label": str(item["label"]), "score": score})
    return sorted(clean, key=lambda x: x["score"], reverse=True)[:3]


def gemini_image_review(raw: bytes, mime_type: str, classifier_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Optional server-side multimodal review. The API key never enters the browser."""
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini review is not configured. Add GEMINI_API_KEY to Streamlit Community Cloud Secrets or a local environment variable.")

    candidate_text = ", ".join(pretty_label(x["label"]) for x in classifier_candidates) or "not available"
    prompt = f"""You are an image-review assistant for a plant-health student prototype. Inspect this leaf photograph carefully.
The specialist classifier's candidate labels, which may be wrong, are: {candidate_text}.
Return ONLY one valid JSON object with these keys:
- plant_or_crop: string, identify only if visually supportable; otherwise 'uncertain'
- visible_observations: array of 2 to 4 short, strictly visual observations (texture, color, spots, edges, image quality); do not invent symptoms not visible
- possible_concerns: array of up to 3 cautious possibilities; describe as possibilities only, never confirmed disease
- image_quality: one of 'good', 'usable', or 'poor', based on focus, lighting, and whether a leaf is visible
- needs_rescan: boolean
- verification_steps: array of 2 to 4 short safe steps, including comparing multiple leaves and consulting a local agricultural expert before treatment
- caution: one short sentence that this image-only review cannot confirm diagnosis and may be wrong
Rules: do not prescribe pesticides, do not provide made-up numerical confidence, do not claim certainty, do not repeat the classifier's candidate labels as ground truth. If the image is not a plant leaf, say so in plant_or_crop and request a relevant image in observations. Keep all output concise."""

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    encoded = base64.b64encode(raw).decode("ascii")
    payload = {
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime_type, "data": encoded}}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2, "maxOutputTokens": 1100},
    }
    response = requests.post(
        endpoint,
        headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=75,
    )
    if response.status_code >= 400:
        detail = ""
        try:
            detail = response.json().get("error", {}).get("message", "")
        except Exception:
            pass
        if response.status_code in (401, 403):
            raise RuntimeError("Gemini rejected the API key or model access. Check the server-side GEMINI_API_KEY secret and your provider access.")
        raise RuntimeError(f"Gemini vision request failed (HTTP {response.status_code}). {detail[:300]}")

    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no review. Check the image and try again.")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "\n".join(str(p.get("text", "")) for p in parts if isinstance(p, dict) and p.get("text"))
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Gemini's response was not valid structured JSON. Retry once or switch to classifier-only mode.") from exc
    if not isinstance(result, dict):
        raise RuntimeError("Gemini returned an unexpected response structure.")

    def strings(key: str, limit: int) -> list[str]:
        value = result.get(key, [])
        if not isinstance(value, list):
            return []
        return [str(x).strip()[:300] for x in value if isinstance(x, (str, int, float)) and str(x).strip()][:limit]

    quality = str(result.get("image_quality", "usable")).lower()
    if quality not in {"good", "usable", "poor"}:
        quality = "usable"
    return {
        "plant_or_crop": str(result.get("plant_or_crop", "uncertain"))[:180],
        "visible_observations": strings("visible_observations", 4),
        "possible_concerns": strings("possible_concerns", 3),
        "image_quality": quality,
        "needs_rescan": bool(result.get("needs_rescan", False)),
        "verification_steps": strings("verification_steps", 4),
        "caution": str(result.get("caution", "This image-only review cannot confirm a plant diagnosis."))[:300],
        "model": GEMINI_MODEL,
    }


def run_analysis(raw: bytes, source: str, filename: str, model_label: str, model_id: str, use_gemini: bool) -> bool:
    try:
        image, fmt, _size = validate_image(raw)
    except ValueError as exc:
        st.error(str(exc))
        return False

    progress_slot = st.empty()
    try:
        with st.status("Preparing the plant-health analysis…", expanded=True) as status:
            progress_slot.progress(8, text="Validating the image…")
            st.write("Image validated · suitable format and size")
            progress_slot.progress(19, text="Loading the specialist classifier…")
            classifier = get_classifier(model_id)
            progress_slot.progress(58, text="Ranking plant-health classes…")
            predictions = normalize_classifier_results(classifier(image, top_k=3))
            if not predictions:
                status.update(label="No usable prediction", state="error")
                st.error("The classifier returned no valid classes. Try another clear leaf photograph.")
                return False

            review = None
            review_error = None
            if use_gemini:
                progress_slot.progress(74, text="Running multimodal visual review…")
                try:
                    review = gemini_image_review(raw, mime_from_format(fmt), predictions)
                except Exception as exc:
                    review_error = str(exc)

            progress_slot.progress(94, text="Building the report…")
            digest = hashlib.sha256(raw).hexdigest()
            quality = assess_capture_quality(image)
            created_at = time.strftime("%Y-%m-%d %H:%M:%S")
            report = {
                "results": predictions,
                "review": review,
                "review_error": review_error,
                "image_hash": digest,
                "source": source,
                "filename": filename,
                "created_at": created_at,
                "model_id": model_id,
                "model_label": model_label,
                "gemini_used": bool(review),
                "quality": quality,
                "field_note": str(st.session_state.get("ag_field_note", "")).strip()[:500],
            }
            st.session_state["ag_report"] = report
            history = list(st.session_state.get("ag_history", []))
            # Session-only notebook stores report metadata, never the image itself.
            history.insert(0, {
                "created_at": created_at,
                "source": source,
                "filename": filename,
                "prediction": predictions[0]["label"],
                "score": predictions[0]["score"],
                "model_id": model_id,
                "image_hash": digest,
                "field_note": report["field_note"],
                "quality_score": quality["score"],
                "candidate_count": len(predictions),
            })
            st.session_state["ag_history"] = history[:12]
            st.session_state["ag_comparison"] = None
            status.update(label="Analysis complete", state="complete", expanded=False)
            progress_slot.progress(100, text="Report ready")
        time.sleep(0.12)
        progress_slot.empty()
        return True
    except Exception as exc:
        progress_slot.empty()
        st.error("The scan could not be completed. The model may still be loading, or the service may be unavailable.")
        with st.expander("Technical details", expanded=False):
            st.code(f"{type(exc).__name__}: {exc}")
        return False


# ---------------------------- ESP32-CAM ----------------------------
def build_device_url(base_url: str, path: str) -> str:
    base = base_url.strip()
    if not base:
        raise ValueError("Enter the ESP32-CAM base URL, such as http://192.168.4.1.")
    if not base.startswith(("http://", "https://")):
        raise ValueError("The camera URL must begin with http:// or https://.")
    return urljoin(base.rstrip("/") + "/", path.strip().lstrip("/"))


def test_esp32(base_url: str, status_path: str, timeout: float) -> tuple[bool, str]:
    try:
        url = build_device_url(base_url, status_path or "/status")
        start = time.perf_counter()
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        latency = (time.perf_counter() - start) * 1000
        return True, f"Status endpoint responded · HTTP {response.status_code} · {latency:.0f} ms."
    except requests.Timeout:
        return False, f"Timed out after {timeout:g}s. Check camera power, Wi-Fi and the endpoint."
    except requests.ConnectionError:
        return False, "Could not reach the camera. If Streamlit is hosted in the cloud, it cannot normally route to a private IP on your home Wi-Fi. Test locally on the same network or use a secure bridge."
    except requests.HTTPError as exc:
        return False, f"Camera endpoint returned an HTTP error: {exc}"
    except Exception as exc:
        return False, f"Connection test failed: {type(exc).__name__}: {exc}"


def capture_esp32(base_url: str, capture_path: str, timeout: float) -> bytes:
    url = build_device_url(base_url, capture_path or "/capture")
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.Timeout as exc:
        raise RuntimeError(f"Capture timed out after {timeout:g}s.") from exc
    except requests.ConnectionError as exc:
        raise RuntimeError("Camera unreachable from the machine running Streamlit. Check the IP and network.") from exc
    except requests.HTTPError as exc:
        raise RuntimeError(f"Camera endpoint returned an HTTP error: {exc}") from exc
    raw = response.content
    validate_image(raw)
    return raw


# ---------------------------- Report renderer ----------------------------
def render_report(report: dict[str, Any]) -> None:
    results = report["results"]
    best = results[0]
    label_html = escaped(pretty_label(best["label"]))
    score = float(best["score"])
    healthy = "healthy" in str(best["label"]).lower()

    st.markdown('<div class="ag-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="ag-kicker">YOUR SCAN IS READY</div><div class="ag-section-title" style="margin-top:.45rem">Plant-health screening report</div><div class="ag-section-sub">Two different signals can help you inspect the sample. Neither is a confirmed diagnosis.</div>', unsafe_allow_html=True)
    left, right = st.columns([1.1, .9], gap="large")
    with left:
        st.markdown(
            f'<div class="ag-report-card"><div class="ag-kicker">SPECIALIST CLASSIFIER · TOP CLASS</div><div class="ag-result-name">{label_html}</div><div class="ag-secondary" style="margin-top:.75rem">The classifier ranked this category highest among its learned labels.</div><div style="margin-top:1rem"><span class="ag-pill">{"Healthy class predicted" if healthy else "Disease-related class predicted"}</span></div></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f'<div class="ag-report-card"><div class="ag-kicker">MODEL OUTPUT SCORE</div><div class="ag-score-value">{score:.1%}</div><div class="ag-track"><div class="ag-fill" style="width:{score * 100:.1f}%"></div></div><div class="ag-secondary" style="margin-top:1rem">This number is the classifier score, <strong style="color:#ffffff">not a calibrated probability</strong> that the label is correct.</div></div>',
            unsafe_allow_html=True,
        )

    quality = report.get("quality") or {}
    if quality:
        quality_col1, quality_col2 = st.columns([1.05, .95], gap="large")
        with quality_col1:
            st.markdown(
                f'<div class="ag-glass" style="margin-top:1rem"><div class="ag-kicker">IMAGE QUALITY HINT</div><div class="ag-quality-score"><div class="ag-quality-title">{escaped(quality.get("label", "Not assessed"))}</div><span class="ag-quality-badge">{int(quality.get("score", 0))}/100</span></div><div class="ag-quality-track"><div class="ag-quality-fill" style="width:{max(0,min(100,int(quality.get("score",0))))}%"></div></div><div class="ag-feature-note">A simple lighting, tonal-contrast and resolution heuristic. It does not detect disease and cannot guarantee a good image.</div></div>',
                unsafe_allow_html=True,
            )
        with quality_col2:
            if report.get("field_note"):
                st.markdown(
                    f'<div class="ag-glass" style="margin-top:1rem"><div class="ag-kicker">YOUR FIELD NOTE</div><div class="ag-secondary" style="margin-top:.65rem">{escaped(report["field_note"])}</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="ag-glass" style="margin-top:1rem"><div class="ag-kicker">NEXT BEST STEP</div><div class="ag-secondary" style="margin-top:.65rem">Compare this result with several leaves from the same plant before drawing a conclusion.</div></div>',
                    unsafe_allow_html=True,
                )

    export_col, status_col = st.columns([1, 1], gap="medium")
    with export_col:
        report_export = {k: v for k, v in report.items() if k != "image_hash"}
        st.download_button(
            "↓  Export this report · JSON",
            data=json.dumps(report_export, ensure_ascii=False, indent=2),
            file_name=f"agriscan-report-{time.strftime('%Y%m%d-%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
            key="ag_export_report_json",
        )
    with status_col:
        st.markdown('<div class="ag-feature-note" style="padding:.55rem 0">Report export includes the model outputs and notes, not the original image.</div>', unsafe_allow_html=True)

    if healthy:
        st.success("The highest-ranked class contains ‘healthy’. This does not rule out disease, pests or other plant stress.")
    else:
        st.warning("A disease-related category ranked first. Verify it independently before considering treatment.")

    st.markdown('<div class="ag-glass-title" style="margin-top:1.5rem">Candidate ranking</div>', unsafe_allow_html=True)
    for index, item in enumerate(results, start=1):
        name = escaped(pretty_label(item["label"]))
        val = float(item["score"])
        st.markdown(
            f'<div class="ag-candidate"><div style="display:flex;align-items:center;gap:.85rem;min-width:0"><div style="display:grid;place-items:center;flex:0 0 36px;height:36px;border-radius:12px;background:rgba(181,221,161,.17);color:#e0f3d3;font-weight:900">{index:02d}</div><div class="ag-candidate-name">{name}</div></div><div class="ag-candidate-score">{val:.1%}</div></div>',
            unsafe_allow_html=True,
        )

    review = report.get("review")
    review_error = report.get("review_error")
    if review:
        st.markdown('<div class="ag-divider"></div><div class="ag-kicker">MULTIMODAL SECOND OPINION</div><div class="ag-section-title" style="font-size:1.35rem;margin-top:.3rem">Advanced vision review</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ag-glass"><div class="ag-stat-label">PLANT / CROP</div><div class="ag-stat-value">{escaped(review.get("plant_or_crop", "uncertain"))}</div><div style="margin-top:1rem"><span class="ag-pill">Image quality: {escaped(review.get("image_quality", "usable")).title()}</span></div></div>', unsafe_allow_html=True)
        obs_col, concern_col = st.columns(2, gap="large")
        with obs_col:
            st.markdown('<div class="ag-glass-title" style="margin-top:1rem">Visible observations</div>', unsafe_allow_html=True)
            observations = review.get("visible_observations", [])
            if observations:
                for item in observations:
                    st.markdown(f'<div class="ag-candidate"><div class="ag-candidate-name">{escaped(item)}</div></div>', unsafe_allow_html=True)
            else:
                st.write("The vision review provided no clear visual observations.")
        with concern_col:
            st.markdown('<div class="ag-glass-title" style="margin-top:1rem">Possibilities to verify</div>', unsafe_allow_html=True)
            concerns = review.get("possible_concerns", [])
            if concerns:
                for item in concerns:
                    st.markdown(f'<div class="ag-candidate"><div class="ag-candidate-name">{escaped(item)}</div></div>', unsafe_allow_html=True)
            else:
                st.write("No specific concerns could be suggested from the image alone.")
        with st.expander("Advanced review · verification steps", expanded=True):
            steps = review.get("verification_steps", [])
            if steps:
                for i, step in enumerate(steps, start=1):
                    st.markdown(f"**{i:02d}.** {step}")
            st.info(str(review.get("caution", "Image review cannot confirm diagnosis.")))
        st.caption(f"Multimodal model: {escaped(review.get('model', GEMINI_MODEL))}. Review is AI-generated and may be mistaken.")
    elif report.get("gemini_used"):
        st.warning("The classifier worked, but the advanced vision review did not complete. The classifier result is available above.")
    elif review_error:
        st.warning(f"Advanced vision review was unavailable; classifier result is shown. Details: {review_error}")

    with st.expander("Research lab · compare both classifiers", expanded=False):
        primary_id = str(report.get("model_id", ""))
        vit_id = MODEL_OPTIONS["Specialist leaf classifier · Vision Transformer"]
        mobile_id = MODEL_OPTIONS["Lightweight fallback · MobileNetV2"]
        if primary_id == vit_id:
            comparison_id = mobile_id
            comparison_name = "Lightweight fallback · MobileNetV2"
        else:
            comparison_id = vit_id
            comparison_name = "Specialist leaf classifier · Vision Transformer"
        st.markdown(
            '<div class="ag-feature-note">Run a second classifier on the same image and compare its top-ranked class. This is an exploratory consistency check, not a way to prove which model is right. The Vision Transformer may take longer to load.</div>',
            unsafe_allow_html=True,
        )
        if st.button("⇄  Compare with the other classifier", use_container_width=True, key="ag_compare_models"):
            current_raw = st.session_state.get("ag_image_bytes")
            if not current_raw or hashlib.sha256(current_raw).hexdigest() != report.get("image_hash"):
                st.warning("The original image is no longer available in this session. Re-select it and run the scan again.")
            else:
                try:
                    with st.spinner(f"Loading {comparison_name} and comparing the same image…"):
                        comparison_image, _, _ = validate_image(current_raw)
                        second_classifier = get_classifier(comparison_id)
                        second_predictions = normalize_classifier_results(second_classifier(comparison_image, top_k=3))
                    if not second_predictions:
                        st.warning("The second classifier returned no valid candidate classes.")
                        st.session_state["ag_comparison"] = None
                    else:
                        st.session_state["ag_comparison"] = {
                            "image_hash": report.get("image_hash"),
                            "primary_model": str(report.get("model_label", primary_id)),
                            "primary_id": primary_id,
                            "primary_results": report.get("results", []),
                            "secondary_model": comparison_name,
                            "secondary_id": comparison_id,
                            "secondary_results": second_predictions,
                        }
                except Exception as exc:
                    st.error("The model comparison could not be completed. The original report remains available.")
                    with st.expander("Comparison technical details", expanded=False):
                        st.code(f"{type(exc).__name__}: {exc}")

        comparison = st.session_state.get("ag_comparison")
        if comparison and comparison.get("image_hash") == report.get("image_hash"):
            primary_predictions = comparison.get("primary_results", [])
            secondary_predictions = comparison.get("secondary_results", [])
            if primary_predictions and secondary_predictions:
                primary_top = primary_predictions[0]
                secondary_top = secondary_predictions[0]
                same_label = str(primary_top.get("label", "")).strip().lower() == str(secondary_top.get("label", "")).strip().lower()
                cmp1, cmp2 = st.columns(2, gap="large")
                with cmp1:
                    st.markdown(
                        f'<div class="ag-report-card"><div class="ag-kicker">MODEL A</div><div class="ag-feature-title" style="margin-top:.65rem">{escaped(comparison.get("primary_model", "Classifier A"))}</div><div class="ag-result-name" style="font-size:1.1rem">{escaped(pretty_label(primary_top["label"]))}</div><div class="ag-score-value" style="font-size:2rem">{float(primary_top["score"]):.1%}</div></div>',
                        unsafe_allow_html=True,
                    )
                with cmp2:
                    st.markdown(
                        f'<div class="ag-report-card"><div class="ag-kicker">MODEL B</div><div class="ag-feature-title" style="margin-top:.65rem">{escaped(comparison.get("secondary_model", "Classifier B"))}</div><div class="ag-result-name" style="font-size:1.1rem">{escaped(pretty_label(secondary_top["label"]))}</div><div class="ag-score-value" style="font-size:2rem">{float(secondary_top["score"]):.1%}</div></div>',
                        unsafe_allow_html=True,
                    )
                if same_label:
                    st.success("Both models ranked the same class first. Agreement is useful evidence to record, but it does not establish correctness.")
                else:
                    st.warning("The models disagreed on the top class. Treat the result as uncertain and verify the sample independently.")
                with st.expander("Show both rankings", expanded=False):
                    rank_col_a, rank_col_b = st.columns(2, gap="large")
                    with rank_col_a:
                        st.markdown(f"**{escaped(comparison.get('primary_model', 'Model A'))}**")
                        for i, candidate in enumerate(primary_predictions, start=1):
                            st.write(f"{i}. {pretty_label(candidate['label'])} · {float(candidate['score']):.1%}")
                    with rank_col_b:
                        st.markdown(f"**{escaped(comparison.get('secondary_model', 'Model B'))}**")
                        for i, candidate in enumerate(secondary_predictions, start=1):
                            st.write(f"{i}. {pretty_label(candidate['label'])} · {float(candidate['score']):.1%}")

    with st.expander("How to interpret this report", expanded=False):
        st.write("The specialist model compares the picture with patterns in its training data and returns ranked classes. A higher score does not prove that a label is correct. Models trained on clean, controlled leaf photos can perform much worse in real fields with variable backgrounds, lighting, crop varieties and unfamiliar disease patterns.")
        st.write("The advanced vision model, when enabled, is a second opinion for image observations—not a lab test or a trained local agronomist. Disagreement between the two outputs is a reason to verify, not to pick whichever sounds more certain.")
    with st.expander("Recommended next steps", expanded=False):
        st.markdown("""
- Inspect both sides of several leaves and compare the same plant and nearby plants.
- Retake a close-up in soft natural light if the image is blurred, dark or crowded.
- Consider pests, water stress, nutrient issues and other causes rather than assuming disease.
- Consult a local agricultural extension officer or qualified plant-health expert before treatment.
- Do not spray chemicals solely on the basis of an AI output.
""")
    st.caption(
        f"Source: {escaped(report.get('source','image'))} · {escaped(report.get('filename','leaf image'))} · "
        f"{escaped(report.get('created_at',''))} · Classifier: {escaped(report.get('model_id','unknown'))}"
    )


# ---------------------------- App layout ----------------------------
init_state()

st.markdown(
    """<div class="ag-nav"><div class="ag-brand"><div class="ag-brand-mark">🌿</div><span>Agriscan AI</span></div><div class="ag-nav-right"><span class="ag-status-dot"></span>PLANT INTELLIGENCE &nbsp;·&nbsp; FIELD LAB 01</div></div>""",
    unsafe_allow_html=True,
)
hero_left, hero_right = st.columns([1.15, .85], gap="large")
with hero_left:
    st.markdown(
        """<section class="ag-hero"><div class="ag-eyebrow">AGRICULTURE &nbsp;·&nbsp; COMPUTER VISION</div><h1>See the leaf.<br><span>Read the signal.</span></h1><p>One thoughtful scan. Multiple clues. A clearer next step. Agriscan combines specialist image classification with optional visual review—while keeping uncertainty visible.</p><div class="ag-hero-tag">✦ &nbsp; AI-assisted screening · Verify before treatment</div></section>""",
        unsafe_allow_html=True,
    )
with hero_right:
    st.markdown(
        """<div class="ag-hero-visual"><div class="ag-visual-label">FIELD INTELLIGENCE · 01</div><div class="ag-orbit"></div><div class="ag-hero-leaf" aria-hidden="true">🍃</div><div class="ag-visual-status"><div><strong>Ready for your sample</strong><span>Capture · Classify · Verify</span></div><span class="ag-live-dot" aria-hidden="true"></span></div></div>""",
        unsafe_allow_html=True,
    )

# Overview stats
s1, s2, s3 = st.columns(3, gap="medium")
with s1:
    st.markdown('<div class="ag-stat"><div class="ag-stat-label">CLASSIFIER</div><div class="ag-stat-value">Vision Transformer</div><div class="ag-stat-note">38 PlantVillage classes · dataset-specific</div></div>', unsafe_allow_html=True)
with s2:
    if GEMINI_API_KEY:
        st.markdown(f'<div class="ag-stat"><div class="ag-stat-label">ADVANCED VISION</div><div class="ag-stat-value">Connected to API</div><div class="ag-stat-note">{escaped(GEMINI_MODEL)} · runs during hybrid scans</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ag-stat"><div class="ag-stat-label">ADVANCED VISION</div><div class="ag-stat-value">Not configured</div><div class="ag-stat-note">Optional Gemini API key stays server-side</div></div>', unsafe_allow_html=True)
with s3:
    d = st.session_state.get("ag_device_status")
    d_label = "Not tested" if d is None else ("Reachable" if d else "Unavailable")
    st.markdown(f'<div class="ag-stat"><div class="ag-stat-label">ESP32-CAM</div><div class="ag-stat-value">{d_label}</div><div class="ag-stat-note">Status changes only after a real connection test.</div></div>', unsafe_allow_html=True)

st.markdown('<div class="ag-divider"></div><div class="ag-section-head"><div><div class="ag-section-title">Scan workspace</div><div class="ag-section-sub">Choose a source, preview the image, and run the AI engines. Upload and browser camera work in the hosted app; ESP32 access depends on the server network.</div></div><span class="ag-pill">● &nbsp; READY TO SCAN</span></div>', unsafe_allow_html=True)

# AI selection: hybrid is offered only if the server-side key is present.
model_labels = list(MODEL_OPTIONS.keys())
if GEMINI_API_KEY:
    engine_options = ["Hybrid · ViT classifier + Gemini 3.1 Pro review", "ViT classifier only", "MobileNetV2 classifier only"]
    default_engine_index = 0
else:
    engine_options = ["ViT classifier only", "MobileNetV2 classifier only"]
    default_engine_index = 0

engine_col, modelinfo_col = st.columns([1.05, .95], gap="large")
with engine_col:
    engine = st.selectbox(
        "AI engine",
        engine_options,
        index=default_engine_index,
        key="ag_engine_select",
        help="Hybrid mode combines a specialist leaf classifier with an optional advanced multimodal visual review. The outputs remain separate because neither confirms a diagnosis.",
    )
if engine.startswith("Hybrid"):
    active_model_id = MODEL_OPTIONS["Specialist leaf classifier · Vision Transformer"]
    active_model_label = "Specialist leaf classifier · Vision Transformer"
    use_gemini = True
elif engine.startswith("MobileNet"):
    active_model_id = MODEL_OPTIONS["Lightweight fallback · MobileNetV2"]
    active_model_label = "Lightweight fallback · MobileNetV2"
    use_gemini = False
else:
    active_model_id = MODEL_OPTIONS["Specialist leaf classifier · Vision Transformer"]
    active_model_label = "Specialist leaf classifier · Vision Transformer"
    use_gemini = False

with modelinfo_col:
    if use_gemini:
        info_title = "Hybrid vision review"
        info_text = "ViT returns the ranked class candidates; Gemini adds cautious visual observations and verification steps. The review may cost API usage and can be wrong."
    elif "MobileNet" in engine:
        info_title = "Lightweight inference"
        info_text = "Smaller local model for faster cold starts or tight memory. Its field performance still needs a labelled test set."
    else:
        info_title = "Specialist leaf classifier"
        info_text = "The PlantVillage-trained ViT is the primary classifier. Benchmark scores on clean dataset images do not establish field accuracy."
    st.markdown(f'<div class="ag-glass" style="height:100%"><div class="ag-kicker">SELECTED ENGINE</div><div class="ag-glass-title" style="font-size:1.14rem;margin-top:.4rem">{escaped(info_title)}</div><div class="ag-secondary">{escaped(info_text)}</div></div>', unsafe_allow_html=True)

if not GEMINI_API_KEY:
    with st.expander("Enable the strongest hybrid review (optional)", expanded=False):
        st.markdown("""
The app can pair its specialist leaf classifier with **Gemini 3.1 Pro** for a separate multimodal visual review. It does not replace the classifier and must not be treated as a definitive diagnosis.

To enable it, configure a Google Gemini API key in **Streamlit Community Cloud → app settings → Secrets** using:

```toml
GEMINI_API_KEY = "your-key"
AGRISCAN_GEMINI_MODEL = "gemini-3.1-pro-preview"
```

For local use, set the same values as environment variables or in a local `.streamlit/secrets.toml` (do not commit that file to GitHub). Never paste API keys into chat or client-visible code. Provider quotas, terms, and potential costs depend on your account; check the official Gemini API docs first.
""")

# Input source
mode = st.radio(
    "Choose image source",
    ["Upload image", "Browser camera", "ESP32-CAM"],
    horizontal=True,
    label_visibility="collapsed",
    key="ag_input_mode",
)

raw: bytes | None = None
source = ""
filename = ""
new_camera_capture = False

if mode == "Upload image":
    input_col, guide_col = st.columns([1.08, .92], gap="large")
    with input_col:
        with st.container(border=True):
            st.markdown('<div class="ag-kicker">01 · IMAGE INPUT</div><div class="ag-glass-title" style="margin-top:.45rem">Upload a leaf photograph</div><div class="ag-secondary">JPG, PNG or WebP · maximum 10 MB</div>', unsafe_allow_html=True)
            uploaded = st.file_uploader("Choose leaf image", type=["jpg", "jpeg", "png", "webp"], key="ag_upload_widget", label_visibility="collapsed")
            if uploaded is not None:
                raw, source, filename = uploaded.getvalue(), "Upload", uploaded.name
    with guide_col:
        st.markdown('<div class="ag-glass"><div class="ag-kicker">BETTER INPUT, BETTER EVIDENCE</div><div class="ag-glass-title" style="margin-top:.45rem">Make the leaf the subject.</div><div class="ag-secondary">Use sharp focus, soft even light, and one clear leaf. Avoid strong color filters and extreme shadows. If symptoms vary, collect a few separate samples.</div><div class="ag-divider"></div><span class="ag-pill">✦ &nbsp; 10 MB image guard</span></div>', unsafe_allow_html=True)

elif mode == "Browser camera":
    camera_col, guide_col = st.columns([1.08, .92], gap="large")
    with camera_col:
        with st.container(border=True):
            st.markdown('<div class="ag-kicker">01 · LIVE CAMERA</div><div class="ag-glass-title" style="margin-top:.45rem">Capture a leaf in frame</div><div class="ag-secondary">Your browser asks for camera permission. A clear close-up works best.</div>', unsafe_allow_html=True)
            auto_camera = st.checkbox("Auto-analyze after a new capture", value=True, key="ag_camera_auto")
            camera_file = st.camera_input("Capture leaf", key="ag_camera_widget", help="Place the leaf in even light and hold the camera still.")
            if camera_file is not None:
                raw, source, filename, new_camera_capture = camera_file.getvalue(), "Browser camera", f"browser-camera-{camera_file.file_id if hasattr(camera_file, 'file_id') else 'capture'}.jpg", True
    with guide_col:
        st.markdown('<div class="ag-glass"><div class="ag-kicker">CAMERA NOTES</div><div class="ag-glass-title" style="margin-top:.45rem">A clean capture sequence.</div><div class="ag-secondary">1. Allow camera access.<br>2. Keep the leaf centered and still.<br>3. Capture once; the same image will not be auto-analyzed repeatedly on every rerun.</div><div class="ag-divider"></div><span class="ag-pill">● &nbsp; Browser permission required</span></div>', unsafe_allow_html=True)

else:
    st.markdown('<div class="ag-glass"><div class="ag-kicker">01 · DEVICE INTEGRATION</div><div class="ag-glass-title" style="margin-top:.45rem">ESP32-CAM connection</div><div class="ag-secondary">These endpoint paths are configurable examples. They must match your friend’s actual firmware.</div></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.25, .9, .9], gap="medium")
    with c1:
        base_url = st.text_input("Camera base URL", value=st.session_state.get("ag_esp32_base_url", "http://192.168.4.1"), key="ag_esp32_base_url", help="Example only. Use the real address assigned by firmware/network.")
    with c2:
        status_path = st.text_input("Status path", value=st.session_state.get("ag_esp32_status_path", "/status"), key="ag_esp32_status_path")
    with c3:
        capture_path = st.text_input("Capture path", value=st.session_state.get("ag_esp32_capture_path", "/capture"), key="ag_esp32_capture_path")
    d1, d2, d3 = st.columns([.7, 1.1, 1.1], gap="medium")
    with d1:
        timeout_s = st.selectbox("Timeout", [3, 5, 8, 12, 20], index=2, key="ag_esp32_timeout")
    with d2:
        preview_before = st.checkbox("Preview before analysis", value=False, key="ag_esp32_preview_first")
    with d3:
        st.write("")
        test_clicked = st.button("Test camera connection", use_container_width=True, key="ag_test_esp32")
    if test_clicked:
        ok, message = test_esp32(base_url, status_path or "/status", float(timeout_s))
        st.session_state["ag_device_status"] = ok
        st.session_state["ag_device_error"] = None if ok else message
        (st.success if ok else st.error)(message)
    st.warning("Cloud-network limitation: a Streamlit Community Cloud server cannot normally reach a private camera IP on your home Wi-Fi. Run Streamlit on a laptop/Raspberry Pi on the same network, or use a secure bridge/API. Do not expose an unauthenticated camera to the public internet.")
    cap_col, cap_note = st.columns([1, 1.4], gap="large")
    with cap_col:
        capture_clicked = st.button("📷  Capture & analyze", type="primary", use_container_width=True, key="ag_capture_esp32")
    with cap_note:
        st.markdown('<div class="ag-secondary" style="padding:.5rem 0">The report starts only after a real, valid image is received. Turn on preview-first if you want to inspect the frame before analysis.</div>', unsafe_allow_html=True)
    if capture_clicked:
        st.session_state["ag_esp32_capture_bytes"] = None
        st.session_state["ag_esp32_pending_autoscan"] = False
        st.session_state["ag_report"] = None
        try:
            with st.spinner("Requesting a fresh frame from the ESP32-CAM…"):
                captured = capture_esp32(base_url, capture_path or "/capture", float(timeout_s))
            raw, source, filename = captured, "ESP32-CAM", f"esp32-capture-{int(time.time())}.jpg"
            st.session_state["ag_last_capture_time"] = time.strftime("%H:%M:%S")
            st.session_state["ag_device_status"] = True
            st.session_state["ag_device_error"] = None
            st.session_state["ag_esp32_capture_bytes"] = captured
            st.session_state["ag_esp32_capture_name"] = filename
            st.session_state["ag_esp32_pending_autoscan"] = not st.session_state.get("ag_esp32_preview_first", False)
        except Exception as exc:
            st.session_state["ag_device_status"] = False
            st.session_state["ag_device_error"] = str(exc)
            st.error(f"Camera capture failed: {exc}")
    if raw is None and st.session_state.get("ag_esp32_capture_bytes"):
        raw = st.session_state["ag_esp32_capture_bytes"]
        source = "ESP32-CAM"
        filename = st.session_state.get("ag_esp32_capture_name", "esp32-capture.jpg")

# Preview and explicit action
if raw is not None:
    try:
        digest, preview_image, image_mime = set_active_image(raw, source, filename)
        image_col, action_col = st.columns([1.1, .9], gap="large")
        with image_col:
            with st.container(border=True):
                st.markdown('<div class="ag-kicker">02 · IMAGE PREVIEW</div><div class="ag-glass-title" style="margin-top:.4rem">Your sample</div>', unsafe_allow_html=True)
                st.image(preview_image, use_container_width=True)
                iw, ih = preview_image.size
                st.caption(f"{filename} · {iw} × {ih}px · {len(raw)/1024:.0f} KB · {source}")
        with action_col:
            quality = assess_capture_quality(preview_image)
            quality_color = "#d7efc7" if quality["score"] >= 80 else ("#f0d99a" if quality["score"] >= 55 else "#ffb9a7")
            quality_notes = " ".join(quality["notes"])
            st.markdown(
                f'<div class="ag-glass" style="margin-bottom:1rem"><div class="ag-kicker">CAPTURE QUALITY CHECK</div><div class="ag-quality-score"><div class="ag-quality-title">{escaped(quality["label"])}</div><span class="ag-quality-badge">{quality["score"]}/100</span></div><div class="ag-quality-track"><div class="ag-quality-fill" style="width:{quality["score"]}%"></div></div><div class="ag-feature-note">{escaped(quality_notes)}</div><div class="ag-feature-note" style="margin-top:.35rem">Lighting, contrast and resolution heuristic—not an AI diagnosis.</div></div>',
                unsafe_allow_html=True,
            )
            with st.container(border=True):
                st.markdown('<div class="ag-kicker">NEXT · RUN YOUR SCAN</div><div class="ag-glass-title" style="font-size:1.35rem;margin-top:.5rem">Ready when you are.</div><div class="ag-secondary">The classifier ranks candidate classes. Optional visual review adds a separate signal; neither confirms a diagnosis.</div>', unsafe_allow_html=True)
                st.text_input("Field note (optional)", key="ag_field_note", placeholder="e.g. tomato plant · north garden · leaf 03")
                st.markdown('<div class="ag-divider"></div>', unsafe_allow_html=True)
                if mode == "ESP32-CAM" and not st.session_state.get("ag_esp32_preview_first", False):
                    st.markdown('<span class="ag-pill">✓ &nbsp; Image captured · auto-analysis requested</span>', unsafe_allow_html=True)
                else:
                    analyze_clicked = st.button("✦  Analyze plant", type="primary", use_container_width=True, key="ag_analyze_manual")
                    if analyze_clicked:
                        run_analysis(raw, source, filename, active_model_label, active_model_id, use_gemini)
                if st.button("Clear sample and report", use_container_width=True, key="ag_clear_image", on_click=clear_active_image):
                    st.rerun()
    except ValueError as exc:
        st.error(str(exc))

# Run one-shot auto-analysis only after successful capture has been saved.
if mode == "ESP32-CAM" and raw is not None and st.session_state.get("ag_esp32_pending_autoscan"):
    st.session_state["ag_esp32_pending_autoscan"] = False
    run_analysis(raw, source, filename, active_model_label, active_model_id, use_gemini)

if mode == "Browser camera" and new_camera_capture and raw is not None and st.session_state.get("ag_camera_auto", True):
    camera_hash = hashlib.sha256(raw).hexdigest()
    if st.session_state.get("ag_last_camera_auto_hash") != camera_hash:
        st.session_state["ag_last_camera_auto_hash"] = camera_hash
        run_analysis(raw, source, filename, active_model_label, active_model_id, use_gemini)

report = st.session_state.get("ag_report")
if report and report.get("image_hash") == st.session_state.get("ag_image_hash"):
    render_report(report)

# ---------------------------- Field notebook + feature overview ----------------------------
st.markdown('<div class="ag-divider"></div><div class="ag-section-head"><div><div class="ag-section-title">A little more than a classifier.</div><div class="ag-section-sub">Useful field tools, kept out of the way until you need them.</div></div></div>', unsafe_allow_html=True)
st.markdown(
    """<div class="ag-feature-grid">
      <div class="ag-feature-card"><div class="ag-feature-icon">◉</div><div class="ag-feature-title">Capture quality hints</div><div class="ag-feature-body">A transparent check for brightness, tonal contrast and resolution before you trust a scan.</div></div>
      <div class="ag-feature-card"><div class="ag-feature-icon">⌁</div><div class="ag-feature-title">Two-model research path</div><div class="ag-feature-body">Switch between the specialist Vision Transformer and a lightweight fallback, then document how they differ.</div></div>
      <div class="ag-feature-card"><div class="ag-feature-icon">↗</div><div class="ag-feature-title">Portable scan reports</div><div class="ag-feature-body">Export report data to JSON and keep a lightweight, session-only notebook of recent results.</div></div>
    </div>""",
    unsafe_allow_html=True,
)

history = st.session_state.get("ag_history", [])
with st.expander(f"Field notebook · {len(history)} scan{'s' if len(history) != 1 else ''} in this session", expanded=bool(history)):
    st.markdown('<div class="ag-feature-note">Recent scan metadata is kept in this Streamlit session only; images are not stored in the notebook. Refreshing or ending the session may clear it.</div>', unsafe_allow_html=True)
    if history:
        rows_for_csv = []
        for record in history[:8]:
            st.markdown(
                f'<div class="ag-history-row"><div><div class="ag-history-name">{escaped(pretty_label(record["prediction"]))}</div><div class="ag-history-meta">{escaped(record["created_at"])} · {escaped(record["source"])} · {escaped(record["filename"])}<br>Model: {escaped(record["model_id"])} · Capture check: {record["quality_score"]}/100</div>{f"<div class='ag-feature-note'>Note: {escaped(record["field_note"])}</div>" if record.get("field_note") else ""}</div><div><div class="ag-history-score">{record["score"]:.1%}</div><div class="ag-feature-note">model score</div></div></div>',
                unsafe_allow_html=True,
            )
            rows_for_csv.append({k: record.get(k, "") for k in ["created_at", "source", "filename", "prediction", "score", "model_id", "quality_score", "field_note"]})
        csv_stream = io.StringIO()
        writer = csv.DictWriter(csv_stream, fieldnames=["created_at", "source", "filename", "prediction", "score", "model_id", "quality_score", "field_note"])
        writer.writeheader()
        writer.writerows(rows_for_csv)
        h1, h2 = st.columns([1, 1], gap="medium")
        with h1:
            st.download_button("↓  Export notebook · CSV", data=csv_stream.getvalue(), file_name="agriscan-field-notebook.csv", mime="text/csv", use_container_width=True, key="ag_export_history")
        with h2:
            if st.button("Clear this session's notebook", use_container_width=True, key="ag_clear_history"):
                st.session_state["ag_history"] = []
                st.rerun()
    else:
        st.markdown('<div class="ag-glass"><div class="ag-glass-title">Your field notebook is ready.</div><div class="ag-secondary">Complete a scan and its result will appear here, ready to export for your competition notes.</div></div>', unsafe_allow_html=True)

with st.expander("ESP32-CAM integration guide", expanded=False):
    st.markdown("""
**What the Streamlit app expects:** a configurable status endpoint returning HTTP 2xx and a capture endpoint returning actual JPEG/PNG/WebP bytes. `/status` and `/capture` are examples; match them to the real firmware.

**Local is simplest:** run Streamlit on the laptop or Raspberry Pi connected to the same Wi-Fi/LAN as the ESP32-CAM. Streamlit Community Cloud runs on a remote server and cannot reach private LAN IP addresses directly. A cloud deployment needs a secure, authenticated bridge/API reachable by the server. Avoid exposing the camera directly to the public internet.

**Robot flow:** robot moves to the plant → stop near the leaf → tap Capture & analyze → camera returns an image → classifier runs → optional Gemini visual review → report appears. That flow still depends on the robot's controller, firmware and camera endpoint actually being implemented and tested.
""")

with st.expander("Model scope, reliability and how to compete honestly", expanded=False):
    st.markdown(f"""
**Classifier:** `{active_model_id}`

The Vision Transformer candidate was trained on PlantVillage: 38 classes across 14 plant species. Its model card notes potential train/test leaf leakage and a mismatch between its controlled images and real field conditions. Its benchmark number is therefore not a reliable estimate for in-field accuracy. Read the [model card](https://huggingface.co/kimcomehome/plantvillage-vit-leaf-disease) before presenting benchmark claims.

**Optional multimodal review:** `{GEMINI_MODEL}`. It helps describe visible image features and verification steps; it is not a validated local plant-disease classifier, and its output may be wrong. API usage, current quota and pricing depend on the provider/account. See the [official Gemini model guide](https://ai.google.dev/gemini-api/docs/models) and [pricing](https://ai.google.dev/gemini-api/docs/pricing).

**Validation plan:** create a labelled set of varied local photos (different light, backgrounds, plant stages and symptom severity), define ground truth with a knowledgeable person, test the same set on each model, and report per-class results and failure cases. Do not make accuracy claims from a few internet images.
""")

st.markdown(f'<div class="ag-footer"><strong>AGRISCAN AI</strong><br>Created by {escaped(PROJECT_CREDIT)}<br>Student innovation prototype · AI-assisted plant-health screening<br>Not a substitute for expert agricultural diagnosis.</div>', unsafe_allow_html=True)
