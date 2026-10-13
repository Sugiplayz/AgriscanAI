# Agriscan AI — Streamlit field prototype

Premium dark forest/sage Streamlit app with deliberate high-contrast styles, restrained animations, image upload/browser camera, a configurable ESP32-CAM server-side capture workflow, a PlantVillage ViT classifier, optional Gemini 3.1 Pro multimodal visual review, and honest limitations.

## Run locally

Use Python 3.11 or 3.12 if possible for PyTorch compatibility.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

The first classifier run may download model weights and take several minutes. The primary specialist model is `kimcomehome/plantvillage-vit-leaf-disease` (PlantVillage-trained, 38 classes). The fallback is `Kathir56/plant-disease-tamilnadu`. Neither benchmark performance nor a high model score guarantees accuracy on local field images. This classifier may confidently assign a class even when the plant/crop is outside its label set.

## Optional Gemini 3.1 Pro multimodal review

Hybrid mode is offered only when a server-side key is configured. It does not replace the trained classifier. It adds visual observations and verification suggestions as a separate signal. The output can be wrong; the app explicitly avoids presenting it as a definitive diagnosis.

For Streamlit Community Cloud, open app settings → Secrets and add:

```toml
GEMINI_API_KEY = "YOUR_API_KEY"
AGRISCAN_GEMINI_MODEL = "gemini-3.1-pro-preview"
```

For local development, use environment variables or `.streamlit/secrets.toml`. **Never commit real keys to GitHub, put them in source code, or paste them into chat.** Check provider terms, quota, data use and current price before enabling API calls. If the user's account requires adult age or consent, have a parent/guardian handle setup; do not bypass account requirements.

## Deploy to the existing Streamlit Community Cloud app

1. Replace the repository's entire `app.py` with this project's `app.py`.
2. Replace `requirements.txt` with the included one.
3. Commit and push to the same GitHub repository connected to the existing app.
4. Wait for the cloud rebuild, then test file upload, camera permission, classifier inference and all interactive controls.
5. If the ViT consumes too much memory or cold-start time, choose the MobileNetV2 fallback from the engine selector.

## ESP32-CAM

The app expects a configurable status path (default `/status`) and a capture path (default `/capture`) that returns raw image bytes. These are examples until firmware is known.

For first integration, run Streamlit on the laptop or Raspberry Pi connected to the same LAN as the ESP32-CAM. Streamlit Community Cloud cannot ordinarily reach a private camera address on home Wi-Fi. A cloud-hosted workflow needs a secure, authenticated bridge/API reachable from the server; do not expose an unauthenticated camera publicly. The controller, firmware endpoints, Wi-Fi arrangement and robot stop/capture sequence must be confirmed and tested.

## Model evaluation for the competition

Test the same labelled set on both classifiers: attached leaves, different backgrounds and light, multiple symptom stages, healthy samples and non-leaf images. Report sample count, class balance, per-class errors and limitations. The ViT model card warns that its PlantVillage evaluation split may contain photos of the same leaf in both train and test and that real-world field accuracy has not been established.
