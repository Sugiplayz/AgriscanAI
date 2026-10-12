
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Agriscan AI | Plant Health",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stApp {
    background: #f5f7f0;
    color: #20372a;
}
.block-container {
    max-width: 1050px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
.hero {
    background: #173e2c;
    color: #f7f8ed;
    padding: 2rem;
    border-radius: 22px;
    margin-bottom: 1.5rem;
}
.hero h1 {
    color: #f7f8ed;
    font-size: 2.5rem;
    margin-bottom: .4rem;
}
.hero p {
    color: #d6e5d5;
}
.eyebrow {
    text-transform: uppercase;
    letter-spacing: 3px;
    font-size: .72rem;
    color: #b9d7a8;
    font-weight: 700;
}
.panel {
    background: white;
    border: 1px solid #e1e8dc;
    border-radius: 16px;
    padding: 1.2rem;
}
div.stButton > button[kind="primary"] {
    background: #286443;
    border: 0;
    border-radius: 10px;
    min-height: 3rem;
    font-weight: 650;
}
div.stButton > button[kind="primary"]:hover {
    background: #194c30;
    color: white;
}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">AGRICULTURE · COMPUTER VISION</div>
  <h1>🌱 Agriscan AI</h1>
  <p>Smarter plant health screening, one leaf at a time.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### Start a plant scan")
st.write(
    "Capture a leaf or upload an existing photograph. "
    "For best results, use a clear, well-lit image of one leaf."
)

upload_tab, camera_tab = st.tabs(
    ["📁 Upload image", "📷 Use camera"]
)

with upload_tab:
    uploaded = st.file_uploader(
        "Choose a leaf photograph",
        type=["jpg", "jpeg", "png"],
        key="upload",
    )

with camera_tab:
    camera_photo = st.camera_input(
        "Position a leaf in the frame",
        key="camera",
    )

image_file = camera_photo if camera_photo is not None else uploaded

if image_file is not None:
    image = Image.open(image_file).convert("RGB")
    image.thumbnail((900, 900))

    left, right = st.columns([1.05, 1])

    with left:
        st.markdown("#### Your sample")
        st.image(image, use_container_width=True)

    with right:
        st.markdown("#### Ready for analysis")
        st.write(
            "The image will be sent to the hosted classifier "
            "when you start the scan."
        )
        st.caption(
            "Avoid blurry images, strong shadows, and leaves "
            "that occupy only a tiny part of the frame."
        )

        scan = st.button(
            "🔍 Analyze plant",
            type="primary",
            use_container_width=True,
        )

    if scan:
        try:
            with st.spinner("Loading AI and analyzing image..."):
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

            best = results[0]
            label = best["label"]
            score = best["score"]
            readable = label.replace("___", " — ").replace("_", " ")

            st.divider()
            st.markdown("### Screening report")

            result_col, score_col = st.columns(2)

            with result_col:
                st.markdown("**Top predicted class**")
                st.subheader(readable)

            with score_col:
                st.metric("Model score", f"{score:.1%}")

            if "healthy" in label.lower():
                st.success(
                    "Healthy class predicted. This does not "
                    "rule out disease or other plant stress."
                )
            else:
                st.warning(
                    "A disease-related class was predicted. "
                    "This is a screening result, not a confirmed "
                    "diagnosis."
                )

            st.markdown("#### Other candidate classes")
            for item in results:
                name = item["label"].replace("___", " — ").replace("_", " ")
                st.write(f"**{name}** · {item['score']:.1%}")

            st.markdown("#### Recommended next steps")
            st.write(
                "Inspect both sides of the leaf and compare "
                "symptoms across several leaves. Consider lighting, "
                "watering, pests, and other possible causes. "
                "Consult a local agricultural expert before "
                "choosing a treatment."
            )

            st.caption(
                "Model scores are not calibrated probabilities. "
                "Accuracy on field photographs has not been "
                "established by this demonstration."
            )

        except Exception:
            st.error(
                "The scan could not be completed. Check the "
                "Streamlit app logs for details."
            )

else:
    st.markdown("""
    <div class="panel">
      <h4>How Agriscan works</h4>
      <p>01 · Capture or upload a leaf image</p>
      <p>02 · AI ranks possible plant-health classes</p>
      <p>03 · Review the result and verify it before treatment</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.caption(
    "AGRISCAN AI · Student innovation prototype · "
    "AI-assisted screening, not a substitute for expert diagnosis"
)
