
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Agriscan AI",
    page_icon="🌱",
    layout="centered"
)

st.title("🌱 Agriscan AI")
st.caption("SMARTER PLANT HEALTH SCREENING")

st.write(
    "Upload a leaf photograph to screen for supported "
    "plant diseases."
)

st.info(
    "Prototype screening only. Results can be wrong, "
    "especially with outdoor or unfamiliar images."
)

@st.cache_resource
def load_classifier():
    from transformers import pipeline

    return pipeline(
        "image-classification",
        model="Kathir56/plant-disease-tamilnadu",
        device=-1
    )

uploaded = st.file_uploader(
    "Choose a leaf photograph",
    type=["jpg", "jpeg", "png"]
)

if uploaded:
    image = Image.open(uploaded).convert("RGB")
    image.thumbnail((768, 768))

    st.image(
        image,
        caption="Your plant sample",
        use_container_width=True
    )

    if st.button("🔍 Analyze plant", type="primary"):
        try:
            with st.spinner("AI is analyzing your image..."):
                classifier = load_classifier()
                results = classifier(image, top_k=3)

            best = results[0]
            label = best["label"]
            confidence = best["score"]

            st.subheader("Screening result")
            st.metric(
                "Predicted class",
                label.replace("___", " — ").replace("_", " "),
                f"{confidence:.1%} model score"
            )

            if "healthy" in label.lower():
                st.success(
                    "The model predicts a healthy class. "
                    "This does not rule out disease."
                )
            else:
                st.warning(
                    "A disease-related class was predicted. "
                    "Confirm the result with a qualified "
                    "agricultural expert before treatment."
                )

            st.subheader("Other predictions")
            for result in results:
                st.write(
                    f"{result['label'].replace('___', ' — ')}"
                    f" — {result['score']:.1%}"
                )

            st.caption(
                "Scores are model outputs, not calibrated "
                "probabilities or measures of disease severity."
            )

        except Exception:
            st.error(
                "Analysis failed. Check the deployed app logs "
                "for model download, memory, or inference errors."
            )

st.divider()
st.caption("AGRISCAN AI · Student innovation prototype")
