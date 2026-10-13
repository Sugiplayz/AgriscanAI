
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Agriscan AI | Plant Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------
# AGRISCAN AI — DARK FOREST / PASTEL SAGE DESIGN SYSTEM
# ---------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #07110c;
    --bg-soft: #0b1911;
    --surface: rgba(24, 43, 31, 0.76);
    --surface-strong: rgba(29, 53, 38, 0.88);
    --sage: #c5e4b4;
    --sage-bright: #d9f2c9;
    --green: #8fbd85;
    --text: #f0f5eb;
    --muted: #a9bbaa;
    --muted-dark: #829886;
    --border: rgba(190, 222, 180, 0.15);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background:
        radial-gradient(ellipse at 12% 5%,
            rgba(85, 132, 63, 0.16), transparent 36%),
        radial-gradient(ellipse at 90% 45%,
            rgba(43, 104, 65, 0.13), transparent 34%),
        linear-gradient(145deg, #07110c 0%, #0b1810 48%, #07120d 100%);
    color: var(--text);
}

[data-testid="stHeader"] {
    background: rgba(7, 17, 12, 0.76);
}

[data-testid="stToolbar"] {
    right: 1rem;
}

#MainMenu, footer {
    visibility: hidden;
}

.block-container {
    max-width: 1320px;
    padding: 1.5rem 2rem 2.5rem;
}

/* TOP NAVIGATION */

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    padding: 0.85rem 0 1.25rem;
    margin-bottom: 1.2rem;
    border-bottom: 1px solid var(--border);
}

.brand {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    color: var(--sage-bright);
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
    font-size: 1.25rem;
    letter-spacing: -0.6px;
}

.brand-icon {
    font-size: 1.7rem;
}

.nav-caption {
    color: var(--muted-dark);
    font-size: 0.78rem;
    letter-spacing: 0.2px;
}

/* HERO */

.hero {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(ellipse at 82% 25%,
            rgba(120, 171, 94, 0.22), transparent 36%),
        linear-gradient(120deg,
            rgba(24, 52, 34, 0.94),
            rgba(12, 31, 20, 0.88));
    border: 1px solid rgba(193, 224, 178, 0.24);
    border-radius: 25px;
    padding: 2.6rem 2.5rem;
    margin-bottom: 2rem;
    box-shadow:
        0 20px 65px rgba(0, 0, 0, 0.18),
        inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.hero::after {
    content: "✳";
    position: absolute;
    right: 7%;
    top: -65px;
    font-size: 18rem;
    line-height: 1;
    color: rgba(191, 226, 170, 0.035);
    pointer-events: none;
}

.eyebrow {
    color: #b5d6a5;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 0.85rem;
}

.hero h1 {
    font-family: 'Manrope', sans-serif;
    color: #f1f6e9 !important;
    font-size: clamp(2.3rem, 5vw, 3.7rem);
    line-height: 1.12;
    font-weight: 800;
    letter-spacing: -2px;
    margin: 0 0 0.75rem;
}

.hero p {
    color: #c2d6bd !important;
    font-size: 1.05rem;
    max-width: 620px;
    line-height: 1.7;
    margin: 0;
}

.hero-tag {
    display: inline-block;
    margin-top: 1.4rem;
    padding: 0.55rem 0.9rem;
    border: 1px solid rgba(199, 230, 183, 0.2);
    border-radius: 999px;
    background: rgba(208, 239, 192, 0.07);
    color: #cce6bf;
    font-size: 0.78rem;
}

/* HEADINGS AND BODY TEXT */

h1, h2, h3, h4, h5, h6 {
    font-family: 'Manrope', sans-serif;
    color: var(--text);
}

.stApp p,
.stApp li,
.stMarkdown,
.stMarkdown p,
.stMarkdown li {
    color: #d0ddd0;
}

.section-heading {
    font-family: 'Manrope', sans-serif;
    color: #eff6e9;
    font-size: 1.35rem;
    font-weight: 750;
    letter-spacing: -0.4px;
    margin-bottom: 0.35rem;
}

.section-subtitle {
    color: var(--muted);
    font-size: 0.9rem;
    line-height: 1.65;
    margin-bottom: 1.35rem;
}

.small-label {
    text-transform: uppercase;
    letter-spacing: 1.8px;
    font-size: 0.68rem;
    font-weight: 700;
    color: #a9c99b;
}

/* GLASS PANELS */

.glass-card {
    background: linear-gradient(
        145deg,
        rgba(31, 55, 39, 0.80),
        rgba(15, 31, 21, 0.78)
    );
    border: 1px solid var(--border);
    border-radius: 21px;
    padding: 1.4rem;
    box-shadow:
        0 14px 40px rgba(0, 0, 0, 0.13),
        inset 0 1px 0 rgba(255, 255, 255, 0.035);
}

.card-heading {
    color: #eff6e9;
    font-family: 'Manrope', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.9rem;
}

/* TABS */

.stTabs [data-baseweb="tab-list"] {
    background: rgba(10, 25, 16, 0.86);
    border: 1px solid var(--border);
    padding: 5px;
    gap: 5px;
    border-radius: 15px;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 11px;
    border: 1px solid transparent;
    color: #b7c9b5;
    padding: 0.65rem 1rem;
}

.stTabs [data-baseweb="tab"] p {
    color: inherit !important;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(
        135deg,
        rgba(144, 191, 129, 0.30),
        rgba(86, 137, 83, 0.22)
    ) !important;
    border: 1px solid rgba(182, 222, 163, 0.30) !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    background: #b7dda5;
}

.stTabs [data-baseweb="tab-border"] {
    background: transparent;
}

/* UPLOADER */

[data-testid="stFileUploader"] {
    background: rgba(7, 19, 12, 0.42);
    border: 1px dashed rgba(173, 211, 156, 0.36);
    border-radius: 17px;
    padding: 0.55rem;
}

[data-testid="stFileUploaderDropzone"] {
    background: rgba(20, 39, 26, 0.55);
    border: 1px dashed rgba(173, 211, 156, 0.25);
    border-radius: 13px;
}

[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span {
    color: #d5e5d0 !important;
}

[data-testid="stFileUploaderDropzone"] button {
    background: #d3e9c5 !important;
    color: #173521 !important;
    border: 0 !important;
    border-radius: 9px !important;
}

/* INPUTS AND WIDGET LABELS */

[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
.stApp label {
    color: #d9e6d4 !important;
}

[data-testid="stCameraInput"] {
    border-radius: 16px;
    overflow: hidden;
}

.stCaption,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    color: #9fb49f !important;
}

/* BUTTONS */

.stButton > button {
    min-height: 3rem;
    border-radius: 13px;
    background: rgba(31, 54, 37, 0.82);
    color: #e2f0dc !important;
    border: 1px solid rgba(184, 219, 166, 0.24);
    font-weight: 650;
    transition: all 160ms ease;
}

.stButton > button:hover {
    border-color: rgba(202, 237, 183, 0.65);
    background: rgba(54, 87, 55, 0.92);
    color: #ffffff !important;
    transform: translateY(-1px);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #bfe1ad, #8fbd85);
    border: 1px solid rgba(220, 246, 207, 0.45);
    color: #132b1b !important;
    font-weight: 800;
    box-shadow: 0 6px 24px rgba(127, 180, 107, 0.13);
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #d5efc5, #a6d69a);
    color: #102719 !important;
    box-shadow: 0 8px 30px rgba(143, 189, 133, 0.2);
}

/* IMAGE PREVIEW */

[data-testid="stImage"] {
    border: 1px solid rgba(187, 222, 170, 0.22);
    border-radius: 16px;
    overflow: hidden;
}

[data-testid="stImage"] img {
    border-radius: 15px;
}

/* DIVIDERS */

hr {
    border-color: rgba(183, 218, 166, 0.14) !important;
    margin-top: 1.7rem;
    margin-bottom: 1.7rem;
}

/* RESULT METRICS */

[data-testid="stMetric"] {
    background: linear-gradient(
        145deg,
        rgba(35, 62, 42, 0.86),
        rgba(17, 36, 23, 0.91)
    );
    border: 1px solid rgba(187, 222, 170, 0.22);
    border-radius: 17px;
    padding: 1.2rem;
}

[data-testid="stMetric"] label,
[data-testid="stMetric"] [data-testid="stMetricLabel"],
[data-testid="stMetric"] [data-testid="stMetricValue"],
[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    color: #e3efdc !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: 'Manrope', sans-serif;
    font-weight: 800;
}

/* SUCCESS AND WARNING MESSAGES */

[data-testid="stAlert"] {
    border-radius: 14px;
    border: 1px solid rgba(190, 222, 180, 0.18);
}

/* WORKFLOW CARDS */

.step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 37px;
    height: 37px;
    border-radius: 50%;
    background: linear-gradient(135deg, #bfe1ad, #6c9d68);
    color: #132d1b;
    font-weight: 800;
    font-size: 0.85rem;
    margin-bottom: 0.7rem;
}

.step-title {
    color: #edf5e7;
    font-weight: 700;
    font-size: 0.91rem;
    margin-bottom: 0.4rem;
}

.step-description {
    color: #a9bda7;
    font-size: 0.82rem;
    line-height: 1.6;
}

/* FOOTER */

.footer {
    text-align: center;
    color: #829986;
    font-size: 0.76rem;
    padding: 0.7rem 0 0.2rem;
    line-height: 1.9;
}

.footer strong {
    color: #b6d5a8;
    letter-spacing: 1px;
}

/* RESPONSIVE */

@media (max-width: 700px) {
    .block-container {
        padding: 1rem 1rem 2rem;
    }

    .hero {
        padding: 1.7rem 1.3rem;
        border-radius: 20px;
    }

    .hero h1 {
        font-size: 2.35rem;
        letter-spacing: -1px;
    }

    .hero::after {
        right: -18%;
        top: 10%;
        font-size: 10rem;
    }

    .navbar {
        align-items: flex-start;
        flex-direction: column;
    }

    .nav-caption {
        font-size: 0.72rem;
    }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown("""
<div class="navbar">
    <div class="brand">
        <span class="brand-icon">🌿</span>
        <span>Agriscan AI</span>
    </div>
    <div class="nav-caption">
        Healthier Plants &nbsp; · &nbsp;
        Better Harvests &nbsp; · &nbsp;
        A Greener Future
    </div>
</div>

<div class="hero">
    <div class="eyebrow">AGRICULTURE &nbsp; · &nbsp; COMPUTER VISION</div>
    <h1>🌱 Agriscan AI</h1>
    <p>
        Smarter plant health screening, one leaf at a time.
        Turn a leaf photograph into an AI-assisted screening report.
    </p>
    <div class="hero-tag">
        ✦ &nbsp; AI-assisted plant health screening
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# SCAN WORKSPACE
# ---------------------------------------------------------

st.markdown(
    '<div class="section-heading">Start a plant scan</div>',
    unsafe_allow_html=True,
)

st.markdown("""
<div class="section-subtitle">
    Capture a leaf or upload an existing photograph.
    Use clear, well-lit images for the best screening experience.
</div>
""", unsafe_allow_html=True)

upload_tab, camera_tab = st.tabs(
    ["📁  Upload image", "📷  Use camera"]
)

with upload_tab:
    uploaded = st.file_uploader(
        "Choose a leaf photograph",
        type=["jpg", "jpeg", "png"],
        key="upload",
        help="Supported formats: JPG, JPEG and PNG.",
    )

with camera_tab:
    camera_photo = st.camera_input(
        "Position a leaf in the frame",
        key="camera",
    )

image_file = (
    camera_photo
    if camera_photo is not None
    else uploaded
)

image = None

if image_file is not None:
    try:
        image = Image.open(image_file).convert("RGB")
        image.thumbnail((1100, 1100))
    except Exception:
        st.error(
            "We couldn't open that image. "
            "Please try another JPG or PNG photograph."
        )
        image = None


# ---------------------------------------------------------
# IMAGE PREVIEW AND ANALYSIS ACTION
# ---------------------------------------------------------

scan = False

if image is not None:
    preview_col, info_col = st.columns(
        [1.05, 1],
        gap="large",
    )

    with preview_col:
        st.markdown(
            '<div class="card-heading">Your sample</div>',
            unsafe_allow_html=True,
        )
        st.image(
            image,
            use_container_width=True,
        )

        st.markdown("""
        <div class="small-label" style="margin-top:0.8rem;">
            IMAGE PREVIEW &nbsp; · &nbsp; RGB
        </div>
        """, unsafe_allow_html=True)

    with info_col:
        st.markdown("""
        <div class="glass-card">
            <div class="small-label">READY FOR ANALYSIS</div>
            <div style="
                font-family:Manrope,sans-serif;
                font-size:1.35rem;
                font-weight:800;
                color:#eef5e7;
                margin-top:0.55rem;
                margin-bottom:0.7rem;">
                Let's inspect your leaf.
            </div>
            <div style="
                color:#b7cbb5;
                font-size:0.9rem;
                line-height:1.8;">
                Agriscan will send the image through its hosted
                image classifier and rank candidate classes.
            </div>
            <div style="
                margin-top:1.2rem;
                padding:0.95rem;
                border-radius:13px;
                background:rgba(187,222,170,0.07);
                border:1px solid rgba(187,222,170,0.13);
                color:#c5d8bf;
                font-size:0.82rem;
                line-height:1.7;">
                ⓘ &nbsp; For clearer results, photograph one
                leaf in natural light. Avoid blur, strong shadows
                and cluttered backgrounds.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        scan = st.button(
            "✦  Analyze plant",
            type="primary",
            use_container_width=True,
        )

else:
    st.markdown("""
    <div class="glass-card">
        <div class="small-label">YOUR NEXT STEP</div>
        <div style="
            font-family:Manrope,sans-serif;
            color:#edf5e7;
            font-size:1.2rem;
            font-weight:750;
            margin-top:0.65rem;">
            Bring a leaf into focus.
        </div>
        <p style="color:#adbfaa;line-height:1.8;margin-top:0.6rem;">
            Upload a leaf photograph using the tab above, or
            open the camera tab to capture one. Your screening
            report will appear here after analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# AI CLASSIFICATION
# ---------------------------------------------------------

if scan and image is not None:
    try:
        with st.spinner(
            "Waking up the classifier and analyzing your sample..."
        ):
            from transformers import pipeline

            @st.cache_resource
            def get_classifier():
                return pipeline(
                    "image-classification",
                    model="Kathir56/plant-disease-tamilnadu",
                    device=-1,
                )

            classifier = get_classifier()
            results = classifier(image, top_k=3)

        if not results:
            st.error(
                "The model returned no predictions. "
                "Try a different, clearly focused leaf photograph."
            )

        else:
            best = results[0]
            label = best["label"]
            score = float(best["score"])

            readable = (
                label.replace("___", " — ")
                .replace("_", " ")
            )

            st.divider()

            st.markdown("""
            <div class="small-label">YOUR SCREENING RESULTS</div>
            <div class="section-heading" style="margin-top:0.5rem;">
                Plant health report
            </div>
            <div class="section-subtitle">
                AI-generated candidate classes for review.
                Verify the result before making treatment decisions.
            </div>
            """, unsafe_allow_html=True)

            result_col, score_col = st.columns(
                [1.35, 1],
                gap="large",
            )

            with result_col:
                st.markdown("""
                <div class="small-label">TOP PREDICTED CLASS</div>
                """, unsafe_allow_html=True)

                st.markdown(
                    f"""
                    <div style="
                        background:linear-gradient(
                            135deg,
                            rgba(37,67,43,0.88),
                            rgba(16,37,23,0.9)
                        );
                        border:1px solid rgba(190,222,180,0.2);
                        border-radius:17px;
                        padding:1.2rem;
                        margin-top:0.5rem;
                        min-height:95px;">
                        <div style="
                            color:#e5f1dd;
                            font-family:Manrope,sans-serif;
                            font-size:1.2rem;
                            font-weight:800;
                            line-height:1.5;
                            overflow-wrap:anywhere;">
                            {readable}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with score_col:
                st.metric(
                    "Model score",
                    f"{score:.1%}",
                )

                st.caption(
                    "Relative model score — not a calibrated "
                    "probability of disease."
                )

            if "healthy" in label.lower():
                st.success(
                    "Healthy is the model's top predicted class. "
                    "This does not rule out disease, pests or "
                    "other plant stress."
                )
            else:
                st.warning(
                    "The model predicted a disease-related class. "
                    "This is a screening result, not a confirmed "
                    "diagnosis."
                )

            # Ranked candidate classes
            st.markdown("""
            <div class="card-heading" style="margin-top:1.5rem;">
                Other candidate classes
            </div>
            """, unsafe_allow_html=True)

            for index, item in enumerate(results, start=1):
                candidate = (
                    item["label"]
                    .replace("___", " — ")
                    .replace("_", " ")
                )
                candidate_score = float(item["score"])

                st.markdown(
                    f"""
                    <div style="
                        display:flex;
                        align-items:center;
                        justify-content:space-between;
                        gap:1rem;
                        background:rgba(24,45,30,0.68);
                        border:1px solid rgba(190,222,180,0.13);
                        border-radius:13px;
                        padding:0.85rem 1rem;
                        margin:0.55rem 0;">
                        <div style="display:flex;align-items:center;gap:0.8rem;">
                            <div style="
                                display:flex;
                                align-items:center;
                                justify-content:center;
                                min-width:31px;
                                height:31px;
                                border-radius:50%;
                                background:rgba(170,211,151,0.13);
                                color:#c6e5b6;
                                font-size:0.8rem;
                                font-weight:800;">
                                {index:02d}
                            </div>
                            <div style="
                                color:#e0ebda;
                                font-size:0.88rem;
                                overflow-wrap:anywhere;">
                                {candidate}
                            </div>
                        </div>
                        <div style="
                            color:#c2e0b2;
                            font-size:0.9rem;
                            font-weight:800;
                            white-space:nowrap;">
                            {candidate_score:.1%}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Guidance
            st.markdown("""
            <div class="glass-card" style="margin-top:1.5rem;">
                <div class="small-label">WHAT TO DO NEXT</div>
                <div style="
                    color:#edf5e7;
                    font-family:Manrope,sans-serif;
                    font-size:1.1rem;
                    font-weight:750;
                    margin-top:0.65rem;">
                    Verify before you treat.
                </div>
                <div style="
                    color:#b9cdb5;
                    font-size:0.9rem;
                    line-height:1.9;
                    margin-top:0.7rem;">
                    01 &nbsp; Inspect both sides of several leaves.<br>
                    02 &nbsp; Compare visible symptoms across the plant.<br>
                    03 &nbsp; Consider pests, watering, lighting and other causes.<br>
                    04 &nbsp; Consult a local agricultural expert before treatment.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.caption(
                "Important limitation: model scores are not "
                "calibrated probabilities. Field accuracy has not "
                "been established by this demonstration. The model "
                "may produce incorrect predictions, especially for "
                "unfamiliar plants, image conditions or classes."
            )

    except Exception:
        st.error(
            "The scan could not be completed. Please try again. "
            "If the problem continues, check the Streamlit app "
            "logs for the technical error."
        )


# ---------------------------------------------------------
# HOW IT WORKS
# ---------------------------------------------------------

st.divider()

st.markdown("""
<div class="section-heading">How Agriscan works</div>
<div class="section-subtitle">
    A simple image-based screening workflow.
</div>
""", unsafe_allow_html=True)

step1, step2, step3 = st.columns(3, gap="medium")

with step1:
    st.markdown("""
    <div class="glass-card">
        <div class="step-number">01</div>
        <div class="step-title">Capture a leaf</div>
        <div class="step-description">
            Upload a photograph or use the camera to provide
            an image of the plant leaf.
        </div>
    </div>
    """, unsafe_allow_html=True)

with step2:
    st.markdown("""
    <div class="glass-card">
        <div class="step-number">02</div>
        <div class="step-title">AI classification</div>
        <div class="step-description">
            The image classifier ranks candidate classes
            from the categories it has learned.
        </div>
    </div>
    """, unsafe_allow_html=True)

with step3:
    st.markdown("""
    <div class="glass-card">
        <div class="step-number">03</div>
        <div class="step-title">Review and verify</div>
        <div class="step-description">
            Examine the output, consider other causes and
            verify the result before taking action.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.markdown("""
<div class="footer">
    <strong>AGRISCAN AI</strong>
    &nbsp; · &nbsp; Student innovation prototype
    <br>
    AI-assisted plant health screening, not a substitute
    for expert agricultural diagnosis.
</div>
""", unsafe_allow_html=True)
