import hashlib
import html
import io
import os
import time
from typing import Any
from urllib.parse import urljoin

import requests
import streamlit as st
from PIL import Image, UnidentifiedImageError


# ------------------------------------------------------------
# AGRISCAN AI — Streamlit-first competition prototype
# ------------------------------------------------------------
MODEL_OPTIONS = {
    "Higher-capacity Vision Transformer (ViT) — default": "kimcomehome/plantvillage-vit-leaf-disease",
    "Lightweight MobileNetV2 — faster fallback": "Kathir56/plant-disease-tamilnadu",
}
# Optional deployment override. If set, it appears as a selectable model too.
ENV_MODEL_ID = os.getenv("AGRISCAN_MODEL_ID", "").strip()
if ENV_MODEL_ID and ENV_MODEL_ID not in MODEL_OPTIONS.values():
    MODEL_OPTIONS["Custom model from AGRISCAN_MODEL_ID"] = ENV_MODEL_ID
DEFAULT_MODEL_LABEL = next(
    (name for name, model_id in MODEL_OPTIONS.items() if model_id == ENV_MODEL_ID),
    "Higher-capacity Vision Transformer (ViT) — default",
)
if ENV_MODEL_ID and ENV_MODEL_ID in MODEL_OPTIONS.values():
    DEFAULT_MODEL_LABEL = next(name for name, model_id in MODEL_OPTIONS.items() if model_id == ENV_MODEL_ID)

MAX_IMAGE_BYTES = 10 * 1024 * 1024
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
PROJECT_CREDIT = "Jayakanth & [Bro’s Name]"  # Personalize when the project partner's name is known.

st.set_page_config(
    page_title="Agriscan AI | Plant Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Use both a Streamlit theme file and carefully-scoped CSS. Explicit text colors
# are deliberate: inherited Streamlit colors caused the prior contrast issue.
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {
  --ag-bg: #07110c;
  --ag-bg-2: #0b1911;
  --ag-card: rgba(20, 39, 27, .94);
  --ag-card-2: rgba(25, 48, 32, .96);
  --ag-sage: #c7e6b5;
  --ag-mint: #d9f0cb;
  --ag-text: #f3f7ef;
  --ag-body: #d4e2d1;
  --ag-muted: #b4c9b2;
  --ag-border: rgba(183, 220, 166, .23);
}

html, body, [class*="css"] { font-family: 'DM Sans', ui-sans-serif, sans-serif; }
.stApp {
  background:
    radial-gradient(ellipse at 9% 2%, rgba(85, 133, 65, .16), transparent 33%),
    radial-gradient(ellipse at 92% 31%, rgba(45, 105, 65, .14), transparent 31%),
    linear-gradient(145deg, #07110c 0%, #0a1810 55%, #07120c 100%) !important;
  color: var(--ag-text) !important;
}
[data-testid="stHeader"] { background: rgba(7, 17, 12, .82) !important; }
[data-testid="stToolbar"] { right: 1rem; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1240px; padding: 1.1rem 2rem 3rem; }

/* Explicit high-contrast defaults for Streamlit-native content */
.stApp, .stApp p, .stApp li, .stApp label,
.stMarkdown, .stMarkdown p, .stMarkdown li,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
  color: var(--ag-body) !important;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stApp [data-testid="stMarkdownContainer"] h1,
.stApp [data-testid="stMarkdownContainer"] h2,
.stApp [data-testid="stMarkdownContainer"] h3,
.stApp [data-testid="stMarkdownContainer"] h4 {
  color: var(--ag-text) !important;
  font-family: 'Manrope', 'DM Sans', sans-serif !important;
  letter-spacing: -.025em;
}
.stCaption, [data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p { color: var(--ag-muted) !important; font-size: .88rem !important; }

/* Header and premium glass hero */
.ag-nav { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.65rem 0 1.1rem; border-bottom:1px solid rgba(190,222,180,.15); margin-bottom:1.25rem; }
.ag-brand { display:flex; align-items:center; gap:.65rem; color:#e5f4db; font-family:'Manrope',sans-serif; font-size:1.15rem; font-weight:800; letter-spacing:-.035em; }
.ag-brand-mark { width:38px; height:38px; display:grid; place-items:center; border-radius:13px; background:linear-gradient(145deg,#c9e8b5,#82b978); color:#102719; box-shadow:0 5px 20px rgba(144,196,124,.15); font-size:1.25rem; }
.ag-nav-right { color:#b9cfb6; font-size:.85rem; text-align:right; }
.ag-hero { position:relative; overflow:hidden; padding:clamp(1.6rem,4vw,3rem); border-radius:26px; border:1px solid rgba(191,224,177,.29); background:radial-gradient(ellipse at 79% 20%,rgba(126,174,95,.22),transparent 35%),linear-gradient(115deg,rgba(29,58,37,.96),rgba(10,29,18,.98)); box-shadow:0 22px 60px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.045); margin-bottom:2rem; }
.ag-hero:after { content:'✳'; position:absolute; right:5%; top:-4.8rem; font-size:17rem; line-height:1; color:rgba(210,237,192,.045); pointer-events:none; }
.ag-eyebrow { position:relative; z-index:1; text-transform:uppercase; letter-spacing:2.5px; font-size:.78rem; font-weight:700; color:#c2e2b2; margin-bottom:.9rem; }
.ag-hero h1 { position:relative; z-index:1; font-family:'Manrope',sans-serif; font-size:clamp(2.45rem,5.2vw,4rem); line-height:1.08; color:#f4f8ee !important; font-weight:800; letter-spacing:-.06em; margin:0 0 .85rem; }
.ag-hero p { position:relative; z-index:1; max-width:700px; color:#d0e1cb !important; font-size:1.08rem; line-height:1.8; margin:0; }
.ag-hero-tag { position:relative; z-index:1; display:inline-flex; margin-top:1.3rem; padding:.55rem .9rem; border:1px solid rgba(203,232,188,.24); background:rgba(210,239,195,.08); border-radius:999px; color:#d4edc7; font-size:.82rem; }
.ag-section-title { color:#f1f6ed; font-family:'Manrope',sans-serif; font-size:1.55rem; line-height:1.3; font-weight:800; letter-spacing:-.035em; }
.ag-section-sub { color:#bdd0b9; font-size:1rem; line-height:1.7; margin-top:.35rem; margin-bottom:1.2rem; }
.ag-kicker { color:#bdddac; text-transform:uppercase; letter-spacing:1.9px; font-size:.76rem; font-weight:800; }
.ag-glass { background:linear-gradient(145deg,rgba(27,51,34,.94),rgba(13,29,19,.96)); border:1px solid var(--ag-border); border-radius:21px; padding:1.3rem; box-shadow:0 16px 40px rgba(0,0,0,.16),inset 0 1px 0 rgba(255,255,255,.035); }
.ag-glass-title { color:#f0f6eb; font-family:'Manrope',sans-serif; font-weight:800; font-size:1.03rem; margin-bottom:.75rem; }
.ag-secondary { color:#bed0ba; font-size:.95rem; line-height:1.8; }
.ag-mini-pill { display:inline-block; padding:.38rem .68rem; border:1px solid rgba(195,226,179,.26); border-radius:999px; background:rgba(181,219,164,.08); color:#d8edce; font-size:.78rem; font-weight:700; }
.ag-report-card { border:1px solid rgba(190,224,176,.25); background:linear-gradient(145deg,rgba(30,58,38,.97),rgba(13,31,20,.98)); padding:1.4rem; border-radius:20px; height:100%; }
.ag-result-name { color:#f5f8f1; font-family:'Manrope',sans-serif; font-size:clamp(1.15rem,2vw,1.65rem); line-height:1.45; font-weight:800; overflow-wrap:anywhere; margin-top:.6rem; }
.ag-score-value { color:#d5efc4; font-family:'Manrope',sans-serif; font-size:2.5rem; font-weight:800; letter-spacing:-.05em; line-height:1.25; }
.ag-track { height:8px; width:100%; border-radius:999px; background:#293d2d; margin-top:.5rem; overflow:hidden; }
.ag-fill { height:100%; border-radius:999px; background:linear-gradient(90deg,#81b974,#d1e9b7); }
.ag-candidate { display:flex; align-items:center; justify-content:space-between; gap:1rem; border:1px solid rgba(187,220,172,.15); border-radius:13px; background:rgba(20,40,26,.78); padding:.85rem 1rem; margin:.55rem 0; }
.ag-candidate-name { color:#e7f0e1; font-size:.97rem; font-weight:600; overflow-wrap:anywhere; }
.ag-candidate-score { color:#cde8bd; font-size:.95rem; font-weight:800; white-space:nowrap; }
.ag-step-num { display:grid; place-items:center; width:38px; height:38px; border-radius:13px; background:linear-gradient(140deg,#cee9bc,#86b97a); color:#122a1a; font-weight:900; margin-bottom:.9rem; }
.ag-step-title { color:#f2f6ed; font-weight:800; font-size:1rem; margin-bottom:.4rem; }
.ag-step-body { color:#bdcfb8; font-size:.94rem; line-height:1.75; }
.ag-footer { padding:1.6rem 0 .4rem; text-align:center; color:#a5bda3; font-size:.82rem; line-height:1.9; }
.ag-footer strong { color:#cde8be; letter-spacing:1px; }

/* Native widgets: explicit surfaces and foregrounds prevent contrast regressions */
div[data-testid="stRadio"] label, div[data-testid="stCheckbox"] label,
[data-testid="stTextInput"] label, [data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label, [data-testid="stFileUploader"] label {
  color:#e2eddd !important; font-size:.95rem !important;
}
div[role="radiogroup"] { gap:.55rem; }
div[role="radiogroup"] label { border:1px solid rgba(190,222,176,.2); border-radius:13px; padding:.65rem .95rem; background:rgba(20,39,26,.8); }
div[role="radiogroup"] label p { color:#e0edda !important; font-weight:700 !important; }
div[role="radiogroup"] label:has(input:checked) { border-color:#a8d596; background:rgba(133,181,115,.2); }
.stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] > div {
  background:#102318 !important; color:#f0f6eb !important; border-color:#526f52 !important; border-radius:12px !important;
}
.stTextInput input::placeholder { color:#a9bea6 !important; }
[data-baseweb="popover"], [data-baseweb="menu"] { background:#13261a !important; }
[role="option"] { color:#f1f6ec !important; }

[data-testid="stFileUploader"] { background:rgba(10,24,15,.72); border:1px dashed rgba(183,220,166,.52); border-radius:17px; padding:.65rem; }
[data-testid="stFileUploaderDropzone"] { background:rgba(21,41,27,.86) !important; border:1px dashed rgba(183,220,166,.35) !important; border-radius:13px !important; }
[data-testid="stFileUploaderDropzone"] p, [data-testid="stFileUploaderDropzone"] span { color:#e1eddb !important; }
[data-testid="stFileUploaderDropzone"] button { background:#c7e6b5 !important; color:#12281a !important; border:1px solid #c7e6b5 !important; border-radius:10px !important; font-weight:800 !important; }
[data-testid="stCameraInput"] { border-radius:16px; overflow:hidden; }
[data-testid="stCameraInput"] button { background:#c7e6b5 !important; color:#14291a !important; }

.stButton > button { min-height:3rem; padding:.6rem 1.1rem; border:1px solid rgba(190,222,176,.35) !important; border-radius:13px !important; background:rgba(26,49,32,.96) !important; color:#f1f7ed !important; font-size:.98rem !important; font-weight:800 !important; transition:transform .16s ease, border-color .16s ease, background .16s ease; }
.stButton > button:hover { background:rgba(45,78,48,.98) !important; border-color:#b9dfa8 !important; color:#fff !important; transform:translateY(-1px); }
.stButton > button[kind="primary"] { background:linear-gradient(135deg,#d6efc6,#a9d596) !important; color:#102819 !important; border:1px solid #d6efc6 !important; box-shadow:0 8px 22px rgba(116,171,100,.15); }
.stButton > button[kind="primary"]:hover { background:linear-gradient(135deg,#e3f7d5,#bce5aa) !important; color:#0b2113 !important; }
.stButton > button:disabled { background:#24372a !important; color:#a8b9a5 !important; border-color:#3d5540 !important; }

/* Critical contrast fix: Streamlit renders the button label inside nested elements.
   The global .stApp p rule uses !important, so set the inner label explicitly too. */
.stApp div[data-testid="stButton"] > button[kind="primary"],
.stApp div[data-testid="stButton"] > button[data-testid="stBaseButton-primary"] {
  background:linear-gradient(135deg,#d6efc6,#a9d596) !important;
  color:#102819 !important;
  -webkit-text-fill-color:#102819 !important;
  border:1px solid #d6efc6 !important;
}
.stApp div[data-testid="stButton"] > button[kind="primary"] *,
.stApp div[data-testid="stButton"] > button[data-testid="stBaseButton-primary"] *,
.stApp button[kind="primary"] p,
.stApp button[kind="primary"] span,
.stApp button[data-testid="stBaseButton-primary"] p,
.stApp button[data-testid="stBaseButton-primary"] span {
  color:#102819 !important;
  -webkit-text-fill-color:#102819 !important;
  opacity:1 !important;
  text-shadow:none !important;
}
.stApp div[data-testid="stButton"] > button[kind="primary"]:hover *,
.stApp div[data-testid="stButton"] > button[data-testid="stBaseButton-primary"]:hover * {
  color:#0b2113 !important;
  -webkit-text-fill-color:#0b2113 !important;
}

.stTabs [data-baseweb="tab-list"] { background:rgba(8,21,13,.9); border:1px solid var(--ag-border); border-radius:15px; padding:5px; gap:5px; }
.stTabs [data-baseweb="tab"] { border-radius:11px; padding:.7rem 1rem; color:#d3e2cd !important; }
.stTabs [data-baseweb="tab"] p { color:inherit !important; font-size:.95rem !important; font-weight:700 !important; }
.stTabs [aria-selected="true"] { background:rgba(141,188,122,.24) !important; border:1px solid rgba(193,228,174,.35) !important; }
.stTabs [data-baseweb="tab-highlight"] { background:#c8e7b7 !important; }

[data-testid="stMetric"] { background:rgba(25,49,32,.96); border:1px solid var(--ag-border); border-radius:16px; padding:1rem; }
[data-testid="stMetric"] label, [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stMetricDelta"] { color:#edf5e8 !important; }
[data-testid="stAlert"] { border-radius:14px !important; }
[data-testid="stExpander"] { border:1px solid rgba(183,220,166,.24) !important; border-radius:15px !important; background:rgba(17,35,22,.72) !important; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p { color:#e6f0e0 !important; font-weight:700 !important; }
.stProgress > div > div > div > div { background:linear-gradient(90deg,#7fb872,#cde8b9) !important; }
hr { border-color:rgba(183,220,166,.19) !important; margin:1.8rem 0 !important; }
:focus-visible { outline:3px solid #c7e6b5 !important; outline-offset:3px !important; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration:.01ms !important; transition-duration:.01ms !important; scroll-behavior:auto !important; } }
@media (max-width:700px) { .block-container { padding:1rem 1rem 2rem; } .ag-nav { align-items:flex-start; flex-direction:column; } .ag-nav-right { text-align:left; } .ag-hero { padding:1.6rem 1.3rem; border-radius:21px; } .ag-hero:after { right:-15%; top:8%; font-size:10rem; } .ag-section-title { font-size:1.35rem; } }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------- Helpers -----------------------------
def init_state() -> None:
    defaults = {
        "ag_report": None,
        "ag_report_hash": None,
        "ag_image_bytes": None,
        "ag_image_source": None,
        "ag_image_name": None,
        "ag_image_hash": None,
        "ag_last_camera_auto_hash": None,
        "ag_device_status": None,
        "ag_device_error": None,
        "ag_last_capture_time": None,
        "ag_esp32_pending_autoscan": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource(show_spinner=False)
def get_classifier(model_id: str):
    from transformers import pipeline

    return pipeline(
        "image-classification",
        model=model_id,
        device=-1,
    )


def pretty_label(label: str) -> str:
    return str(label).replace("___", " — ").replace("_", " ").strip()


def safe_label(label: str) -> str:
    return html.escape(pretty_label(label))


def validate_image(raw: bytes) -> tuple[Image.Image, str, tuple[int, int]]:
    if not raw:
        raise ValueError("The image file is empty.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("This image is larger than 10 MB. Please resize it or choose a smaller image.")
    try:
        image = Image.open(io.BytesIO(raw))
        image.verify()
        image = Image.open(io.BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("This file does not appear to be a valid JPG, PNG or WebP image.") from exc
    image_format = Image.open(io.BytesIO(raw)).format or "Unknown"
    return image, image_format, image.size


def clear_active_image() -> None:
    """Clear captured/uploaded image state; called before Streamlit reruns widgets."""
    for key in (
        "ag_image_bytes", "ag_image_source", "ag_image_name", "ag_image_hash",
        "ag_report", "ag_report_hash", "ag_esp32_capture_bytes", "ag_esp32_capture_name",
        "ag_esp32_pending_autoscan", "ag_last_camera_auto_hash",
    ):
        st.session_state[key] = None
    # These are widget values; callbacks run before the next script execution.
    for key in ("ag_upload_image", "ag_camera_capture"):
        if key in st.session_state:
            st.session_state[key] = None


def set_active_image(raw: bytes, source: str, filename: str) -> tuple[str, Image.Image]:
    image, _fmt, _size = validate_image(raw)
    digest = hashlib.sha256(raw).hexdigest()
    if st.session_state.get("ag_image_hash") != digest:
        st.session_state["ag_report"] = None
        st.session_state["ag_report_hash"] = None
    st.session_state["ag_image_bytes"] = raw
    st.session_state["ag_image_source"] = source
    st.session_state["ag_image_name"] = filename
    st.session_state["ag_image_hash"] = digest
    return digest, image


def run_analysis(raw: bytes, source: str, filename: str, model_id: str) -> bool:
    try:
        image, _fmt, _size = validate_image(raw)
    except ValueError as exc:
        st.error(str(exc))
        return False

    try:
        with st.spinner("Loading the classifier and analyzing your leaf…"):
            classifier = get_classifier(model_id)
            results = classifier(image, top_k=3)
        if not isinstance(results, list) or not results:
            st.error("The classifier returned no candidate classes. Try a clearer image.")
            return False

        clean_results: list[dict[str, Any]] = []
        for result in results[:3]:
            if not isinstance(result, dict) or "label" not in result or "score" not in result:
                continue
            try:
                score = float(result["score"])
            except (TypeError, ValueError):
                continue
            if not (0 <= score <= 1):
                continue
            clean_results.append({"label": str(result["label"]), "score": score})

        if not clean_results:
            st.error("The classifier response was not in the expected format. Please try again.")
            return False
        clean_results.sort(key=lambda item: item["score"], reverse=True)

        digest = hashlib.sha256(raw).hexdigest()
        st.session_state["ag_report"] = {
            "results": clean_results,
            "image_hash": digest,
            "source": source,
            "filename": filename,
            "created_at": time.strftime("%H:%M:%S"),
            "model_id": model_id,
        }
        st.session_state["ag_report_hash"] = digest
        return True
    except Exception as exc:
        st.error("The scan could not be completed. The classifier may still be loading or the service may be unavailable.")
        with st.expander("Technical details (for troubleshooting)"):
            st.code(f"{type(exc).__name__}: {exc}")
        return False


def build_device_url(base_url: str, path: str) -> str:
    base = base_url.strip()
    if not base:
        raise ValueError("Enter the ESP32-CAM base URL first, such as http://192.168.4.1.")
    if not base.startswith(("http://", "https://")):
        raise ValueError("The device address must begin with http:// or https://.")
    return urljoin(base.rstrip("/") + "/", path.strip().lstrip("/"))


def test_esp32(base_url: str, status_path: str, timeout: float) -> tuple[bool, str]:
    try:
        url = build_device_url(base_url, status_path or "/status")
        start = time.perf_counter()
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        latency = (time.perf_counter() - start) * 1000
        return True, f"Status endpoint responded (HTTP {response.status_code}, {latency:.0f} ms)."
    except requests.Timeout:
        return False, f"Timed out after {timeout:g}s. Check camera power, Wi-Fi and the address."
    except requests.ConnectionError:
        return False, "Could not reach the camera. Check the IP address and network. If this app is hosted on Streamlit Community Cloud, it cannot directly reach a private camera IP on your home Wi-Fi."
    except requests.HTTPError as exc:
        return False, f"The camera returned an HTTP error: {exc}"
    except Exception as exc:
        return False, f"Connection check failed: {type(exc).__name__}: {exc}"


def capture_esp32(base_url: str, capture_path: str, timeout: float) -> bytes:
    url = build_device_url(base_url, capture_path or "/capture")
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.Timeout as exc:
        raise RuntimeError(f"The camera capture timed out after {timeout:g}s.") from exc
    except requests.ConnectionError as exc:
        raise RuntimeError("The camera is unreachable from the machine running Streamlit. Check the IP and Wi-Fi.") from exc
    except requests.HTTPError as exc:
        raise RuntimeError(f"The camera endpoint returned an HTTP error: {exc}") from exc
    content_type = response.headers.get("Content-Type", "").lower()
    raw = response.content
    if not content_type.startswith("image/"):
        # Some simple ESP32 examples omit the image/jpeg Content-Type; validate actual bytes too.
        try:
            validate_image(raw)
        except ValueError as exc:
            raise RuntimeError(f"The capture endpoint did not return a valid image (Content-Type: {content_type or 'not provided'}). Configure it to return image/jpeg bytes.") from exc
    validate_image(raw)
    return raw


def report_html(results: list[dict[str, Any]]) -> None:
    best = results[0]
    best_label = safe_label(best["label"])
    best_score = float(best["score"])
    is_healthy = "healthy" in str(best["label"]).lower()
    st.markdown("<div class='ag-kicker'>SCREENING REPORT</div>", unsafe_allow_html=True)
    st.markdown("<div class='ag-section-title' style='margin-top:.4rem'>Your plant-health results</div>", unsafe_allow_html=True)
    st.markdown("<div class='ag-section-sub'>These are the classifier's leading candidate classes, not a confirmed diagnosis.</div>", unsafe_allow_html=True)

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.markdown(
            f"""<div class="ag-report-card"><div class="ag-kicker">TOP PREDICTED CLASS</div>
            <div class="ag-result-name">{best_label}</div>
            <div style="color:#c2d7bc;font-size:.91rem;line-height:1.7;margin-top:.8rem">The model ranked this class first for the supplied image.</div>
            <div style="margin-top:1rem"><span class="ag-mini-pill">{'Healthy class predicted' if is_healthy else 'Disease-related class predicted'}</span></div></div>""",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""<div class="ag-report-card"><div class="ag-kicker">MODEL SCORE</div>
            <div class="ag-score-value">{best_score:.1%}</div>
            <div class="ag-track"><div class="ag-fill" style="width:{best_score * 100:.1f}%"></div></div>
            <div style="color:#c2d7bc;font-size:.9rem;line-height:1.75;margin-top:1rem">This score reflects the model output. It is <strong style="color:#f0f7ea">not a calibrated probability</strong> that the prediction is correct.</div></div>""",
            unsafe_allow_html=True,
        )

    if is_healthy:
        st.success("The model's top class is labelled healthy. This does not rule out disease, pests or other plant stress.")
    else:
        st.warning("A disease-related class is the model's top prediction. Verify it before choosing any treatment.")

    st.markdown("<div class='ag-glass-title' style='margin-top:1.3rem'>Other candidate classes</div>", unsafe_allow_html=True)
    for index, item in enumerate(results, start=1):
        name = safe_label(item["label"])
        score = float(item["score"])
        st.markdown(
            f"""<div class="ag-candidate"><div style="display:flex;align-items:center;gap:.8rem;min-width:0">
            <div style="display:grid;place-items:center;flex:0 0 34px;height:34px;border-radius:11px;background:rgba(181,221,161,.15);color:#d3ebc4;font-weight:900">{index:02d}</div>
            <div class="ag-candidate-name">{name}</div></div><div class="ag-candidate-score">{score:.1%}</div></div>""",
            unsafe_allow_html=True,
        )

    with st.expander("How should I interpret this report?", expanded=True):
        st.write("The classifier compares the image with visual patterns learned from its training data and ranks candidate classes. A high score does not guarantee that a label is correct, and the model may perform differently on real farm photographs than on its training images.")
        st.write("Field accuracy has not been established for this demonstration. Treat the result as a prompt for further inspection, not proof of a disease.")
    with st.expander("Recommended next steps"):
        st.markdown("""
- Inspect both sides of several leaves, not just one.
- Compare the same pattern across multiple leaves and plants.
- Consider watering, lighting, pests, nutrient issues and other possible causes.
- Ask a local agricultural extension officer or qualified expert before applying a treatment.
- Do not spray chemicals solely on the basis of this AI output.
""")
    report_state = st.session_state.get("ag_report", {})
    model_used = html.escape(str(report_state.get("model_id", "not recorded")))
    st.caption(
        f"Source: {html.escape(str(report_state.get('source', 'image')))} · "
        f"{html.escape(str(report_state.get('filename', 'leaf image')))} · "
        f"{report_state.get('created_at', '')} · Model: {model_used}"
    )


# ----------------------------- State ------------------------------
init_state()

# ----------------------------- Header -----------------------------
st.markdown(
    """<div class="ag-nav"><div class="ag-brand"><div class="ag-brand-mark">🌿</div><span>Agriscan AI</span></div>
    <div class="ag-nav-right">PLANT INTELLIGENCE &nbsp; · &nbsp; STUDENT INNOVATION</div></div>
    <section class="ag-hero"><div class="ag-eyebrow">AGRICULTURE &nbsp; · &nbsp; COMPUTER VISION</div>
    <h1>Plant health,<br>in clearer focus.</h1>
    <p>Capture a leaf, run an AI-assisted screen, and review the evidence before making a decision. Clear results. Honest limitations. Better next steps.</p>
    <div class="ag-hero-tag">✦ &nbsp; AI-assisted screening · Expert verification recommended</div></section>""",
    unsafe_allow_html=True,
)

# Model selector — high-capacity vision model first, compact fallback available.
model_row_left, model_row_right = st.columns([1.05, 1], gap="medium")
with model_row_left:
    model_choice = st.selectbox(
        "AI model engine",
        options=list(MODEL_OPTIONS.keys()),
        index=list(MODEL_OPTIONS.keys()).index(DEFAULT_MODEL_LABEL),
        key="ag_model_choice",
        help="The ViT has more parameters and may take longer to download/start. Use MobileNetV2 if the cloud app runs out of memory or loads too slowly.",
    )
active_model_id = MODEL_OPTIONS[model_choice]
with model_row_right:
    if "Vision Transformer" in model_choice:
        model_note = "Higher-capacity candidate · slower first load · field accuracy still unverified"
    elif "MobileNetV2" in model_choice:
        model_note = "Compact fallback · faster load · field accuracy still unverified"
    else:
        model_note = "Custom model selected from AGRISCAN_MODEL_ID · verify labels and compatibility"
    st.markdown(
        f"<div class='ag-glass' style='height:100%'><div class='ag-kicker'>SELECTED MODEL</div>"
        f"<div class='ag-glass-title' style='margin-top:.45rem;overflow-wrap:anywhere'>{html.escape(model_choice)}</div>"
        f"<div class='ag-secondary'>{html.escape(model_note)}</div></div>",
        unsafe_allow_html=True,
    )

# Status strip
status_col1, status_col2, status_col3 = st.columns(3, gap="medium")
with status_col1:
    st.markdown(f"<div class='ag-glass'><div class='ag-kicker'>MODEL</div><div class='ag-glass-title' style='margin-top:.45rem'>Plant classifier</div><div class='ag-secondary'>{html.escape(active_model_id)} · CPU inference</div></div>", unsafe_allow_html=True)
with status_col2:
    device_status = st.session_state.get("ag_device_status")
    label = "Not tested" if device_status is None else ("Reachable" if device_status else "Unavailable")
    tone = "#d2e9c2" if device_status else ("#f0cf8b" if device_status is False else "#c3d7be")
    st.markdown(f"<div class='ag-glass'><div class='ag-kicker'>ESP32-CAM</div><div class='ag-glass-title' style='margin-top:.45rem;color:{tone}'>{label}</div><div class='ag-secondary'>Connection status updates after a real test.</div></div>", unsafe_allow_html=True)
with status_col3:
    st.markdown("<div class='ag-glass'><div class='ag-kicker'>PRINCIPLE</div><div class='ag-glass-title' style='margin-top:.45rem'>No invented results</div><div class='ag-secondary'>The report appears only after the model returns valid predictions.</div></div>", unsafe_allow_html=True)

st.write("")
st.markdown("<div class='ag-section-title'>Scan workspace</div><div class='ag-section-sub'>Choose an input source. Upload and browser-camera modes work in the hosted app; ESP32 access depends on where Streamlit is running.</div>", unsafe_allow_html=True)

mode = st.radio(
    "Choose input source",
    ["Upload image", "Browser camera", "ESP32-CAM"],
    horizontal=True,
    label_visibility="collapsed",
    key="ag_input_mode",
)

raw: bytes | None = None
source = ""
filename = ""
new_camera_capture = False
capture_error = None

# ----------------------------- Input modes ------------------------
if mode == "Upload image":
    upload_left, upload_right = st.columns([1.1, .9], gap="large")
    with upload_left:
        st.markdown("<div class='ag-glass-title'>Choose a leaf photograph</div><div class='ag-secondary'>Use JPG, PNG or WebP. Maximum file size: 10 MB.</div>", unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload leaf image",
            type=["jpg", "jpeg", "png", "webp"],
            key="ag_upload_image",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            raw = uploaded.getvalue()
            source = "Upload"
            filename = uploaded.name
    with upload_right:
        st.markdown("<div class='ag-glass'><div class='ag-kicker'>PHOTO CHECKLIST</div><div class='ag-glass-title' style='margin-top:.6rem'>A stronger sample starts here</div><div class='ag-secondary'>Use a sharp image, natural even light, one leaf in focus, and as little background clutter as possible. If symptoms vary, inspect several leaves.</div></div>", unsafe_allow_html=True)

elif mode == "Browser camera":
    camera_left, camera_right = st.columns([1.1, .9], gap="large")
    with camera_left:
        st.markdown("<div class='ag-glass-title'>Capture with your device camera</div><div class='ag-secondary'>Allow camera permission when the browser asks. Capture a clear, close view of the leaf.</div>", unsafe_allow_html=True)
        auto_camera = st.checkbox("Automatically analyze after capture", value=True, key="ag_camera_auto")
        camera_file = st.camera_input("Capture a leaf photograph", key="ag_camera_capture")
        if camera_file is not None:
            raw = camera_file.getvalue()
            source = "Browser camera"
            filename = f"browser-camera-{camera_file.file_id if hasattr(camera_file, 'file_id') else 'capture'}.jpg"
            new_camera_capture = True
    with camera_right:
        st.markdown("<div class='ag-glass'><div class='ag-kicker'>CAMERA MODE</div><div class='ag-glass-title' style='margin-top:.6rem'>One capture, then analysis</div><div class='ag-secondary'>With auto-analysis enabled, Agriscan analyzes a newly captured image once. You can turn that off to inspect the preview first.</div></div>", unsafe_allow_html=True)

else:
    st.markdown("<div class='ag-glass'><div class='ag-kicker'>DEVICE SETUP</div><div class='ag-glass-title' style='margin-top:.5rem'>Connect your ESP32-CAM</div><div class='ag-secondary'>Enter the camera address and the endpoints provided by the firmware. Defaults are examples only; your friend’s firmware may use different routes.</div></div>", unsafe_allow_html=True)
    cfg1, cfg2, cfg3 = st.columns([1.35, 1, 1], gap="medium")
    with cfg1:
        base_url = st.text_input("Camera base URL", value=st.session_state.get("ag_esp32_base_url", "http://192.168.4.1"), key="ag_esp32_base_url", help="Example only. Use the actual IP/domain printed or configured by your camera firmware.")
    with cfg2:
        status_path = st.text_input("Status path", value=st.session_state.get("ag_esp32_status_path", "/status"), key="ag_esp32_status_path")
    with cfg3:
        capture_path = st.text_input("Capture path", value=st.session_state.get("ag_esp32_capture_path", "/capture"), key="ag_esp32_capture_path")
    dcol1, dcol2, dcol3 = st.columns([1, 1, 1.25], gap="medium")
    with dcol1:
        timeout_s = st.selectbox("Timeout", [3, 5, 8, 12, 20], index=2, key="ag_esp32_timeout")
    with dcol2:
        preview_before = st.checkbox("Preview before analyzing", value=False, key="ag_esp32_preview_first")
    with dcol3:
        st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
        test_clicked = st.button("Test camera connection", use_container_width=True, key="ag_test_esp32")
    if test_clicked:
        ok, message = test_esp32(base_url, status_path or "/status", float(timeout_s))
        st.session_state["ag_device_status"] = ok
        st.session_state["ag_device_error"] = None if ok else message
        (st.success if ok else st.error)(message)

    st.info("Network reality check: a Streamlit Community Cloud server cannot directly reach a private IP on your home Wi‑Fi. For local ESP32 testing, run Streamlit on a laptop/Raspberry Pi on the same network, or use a secure bridge reachable by the hosted app. Avoid exposing the camera directly to the public internet.")
    c1, c2 = st.columns([1, 1.4], gap="medium")
    with c1:
        capture_clicked = st.button("📷  Capture & analyze", type="primary", use_container_width=True, key="ag_capture_esp32")
    with c2:
        st.markdown("<div class='ag-secondary' style='padding:.45rem 0'>A successful JPEG capture is required before analysis can start.</div>", unsafe_allow_html=True)
    if capture_clicked:
        st.session_state["ag_esp32_capture_bytes"] = None
        st.session_state["ag_esp32_pending_autoscan"] = False
        st.session_state["ag_report"] = None
        st.session_state["ag_report_hash"] = None
        try:
            with st.spinner("Requesting a fresh image from the ESP32-CAM…"):
                captured = capture_esp32(base_url, capture_path or "/capture", float(timeout_s))
            raw = captured
            source = "ESP32-CAM"
            filename = f"esp32-capture-{int(time.time())}.jpg"
            st.session_state["ag_last_capture_time"] = time.strftime("%H:%M:%S")
            st.session_state["ag_device_status"] = True
            st.session_state["ag_device_error"] = None
            st.session_state["ag_esp32_capture_bytes"] = captured
            st.session_state["ag_esp32_capture_name"] = filename
            st.session_state["ag_esp32_pending_autoscan"] = not preview_before
        except Exception as exc:
            st.session_state["ag_device_status"] = False
            st.session_state["ag_device_error"] = str(exc)
            st.error(f"Camera capture failed: {exc}")

    # Retain the most recent camera image so the user can preview and analyze it later.
    if raw is None and st.session_state.get("ag_esp32_capture_bytes"):
        raw = st.session_state["ag_esp32_capture_bytes"]
        source = "ESP32-CAM"
        filename = st.session_state.get("ag_esp32_capture_name", "esp32-capture.jpg")

# ----------------------------- Preview and run --------------------
if raw is not None:
    try:
        digest, preview_image = set_active_image(raw, source, filename)
        preview_col, action_col = st.columns([1.1, .9], gap="large")
        with preview_col:
            st.markdown("<div class='ag-glass-title'>Image preview</div>", unsafe_allow_html=True)
            st.image(preview_image, use_container_width=True)
            w, h = preview_image.size
            st.caption(f"{filename} · {w} × {h} px · {len(raw) / 1024:.0f} KB · {source}")
        with action_col:
            st.markdown("<div class='ag-glass'><div class='ag-kicker'>READY FOR ANALYSIS</div><div class='ag-glass-title' style='font-size:1.3rem;margin-top:.5rem'>Inspect this leaf.</div><div class='ag-secondary'>The classifier will rank its top candidate classes. Results can be wrong, so verify before acting.</div></div>", unsafe_allow_html=True)
            st.write("")
            if mode == "ESP32-CAM" and not st.session_state.get("ag_esp32_preview_first", False):
                st.success("Capture received. Automatic analysis was requested.")
            else:
                if st.button("✦  Analyze plant", type="primary", use_container_width=True, key="ag_analyze_manual"):
                    run_analysis(raw, source, filename, active_model_id)
            st.button("Clear image and report", use_container_width=True, key="ag_clear_image", on_click=clear_active_image)
    except ValueError as exc:
        st.error(str(exc))

# ESP32 capture auto-scan happens only after the image has been validated and
# stored as the active image; doing it earlier would clear the report on rerun.
if mode == "ESP32-CAM" and raw is not None and st.session_state.get("ag_esp32_pending_autoscan"):
    st.session_state["ag_esp32_pending_autoscan"] = False
    run_analysis(raw, source, filename, active_model_id)

# Newly captured browser image: auto-analyze just once per unique image.
if mode == "Browser camera" and new_camera_capture and raw is not None and st.session_state.get("ag_camera_auto", True):
    camera_hash = hashlib.sha256(raw).hexdigest()
    if st.session_state.get("ag_last_camera_auto_hash") != camera_hash:
        st.session_state["ag_last_camera_auto_hash"] = camera_hash
        run_analysis(raw, source, filename, active_model_id)

# Show the latest report only for the image that produced it.
report = st.session_state.get("ag_report")
if report and report.get("image_hash") == st.session_state.get("ag_image_hash"):
    st.divider()
    report_html(report["results"])

# ----------------------------- Integration guide ------------------
st.divider()
st.markdown("<div class='ag-section-title'>Designed for a real field workflow</div><div class='ag-section-sub'>A beautiful interface is step one. A dependable camera connection and carefully tested model are the next milestones.</div>", unsafe_allow_html=True)
step1, step2, step3 = st.columns(3, gap="medium")
with step1:
    st.markdown("<div class='ag-glass'><div class='ag-step-num'>01</div><div class='ag-step-title'>Capture the leaf</div><div class='ag-step-body'>Use a photo upload, browser camera, or a configured ESP32-CAM endpoint. Keep the leaf in focus.</div></div>", unsafe_allow_html=True)
with step2:
    st.markdown("<div class='ag-glass'><div class='ag-step-num'>02</div><div class='ag-step-title'>Rank possible classes</div><div class='ag-step-body'>The hosted classifier returns up to three candidate labels and model scores. Scores are not calibrated probabilities.</div></div>", unsafe_allow_html=True)
with step3:
    st.markdown("<div class='ag-glass'><div class='ag-step-num'>03</div><div class='ag-step-title'>Verify before action</div><div class='ag-step-body'>Review more than one leaf, consider other causes and consult an agricultural expert before treatment.</div></div>", unsafe_allow_html=True)

with st.expander("ESP32-CAM integration — what needs to be true", expanded=False):
    st.markdown("""
**The app side:** it can request a status URL and a capture URL that returns an actual JPEG/PNG/WebP image. The routes above are configurable; they are not assumptions about your friend's firmware.

**The camera/firmware side:** the ESP32-CAM needs power, Wi-Fi/network configuration, and firmware that implements the selected endpoints. The status route should return HTTP 2xx when ready; the capture route should return image bytes. If you eventually call it from a browser directly, the firmware must also handle CORS. This Streamlit version makes requests server-side, so browser CORS is not the same constraint — the machine running Streamlit must itself be able to reach the camera.

**The easiest reliable first integration:** run this Streamlit app on the laptop or Raspberry Pi that is on the same local network as the ESP32-CAM. A cloud-hosted Streamlit app normally cannot route to a private local IP. For a hosted app, use a secure bridge/API with authentication and avoid exposing the camera publicly.

**One-button user experience:** in ESP32-CAM mode, “Capture & analyze” requests the image and runs the classifier only after a valid image is received. Enable “Preview before analyzing” to inspect the frame first.
""")

with st.expander("Model and validation notes", expanded=False):
    st.markdown(f"""
**Currently selected model ID:** `{html.escape(active_model_id)}`

A higher-capacity Vision Transformer is selected by default as a candidate to compare against the original lightweight MobileNetV2. Larger models are not automatically more accurate on real farm photographs. Public benchmark numbers for PlantVillage are not guarantees of performance in the field; different image backgrounds, crop varieties, lighting and unseen diseases can change results substantially.

Model scores are not calibrated probabilities. Before claiming which model is better, test both on the same labelled set of varied images and compare top-1 accuracy, per-class errors, and how often the model confidently gets an example wrong. If the ViT times out or exceeds the Streamlit Cloud memory limit, switch to MobileNetV2 using the model selector above.

A serious competition demo should record each test image, expected label, top prediction and correctness. Do not report accuracy from a handful of hand-picked internet photos as general real-world accuracy.
""")

st.markdown(
    f"""<div class='ag-footer'><strong>AGRISCAN AI</strong><br>
    Created by {html.escape(PROJECT_CREDIT)}<br>
    Student innovation prototype · AI-assisted plant-health screening<br>
    Not a substitute for expert agricultural diagnosis.</div>""",
    unsafe_allow_html=True,
)
