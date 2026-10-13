# Agriscan AI — Streamlit edition

A dark forest / pastel sage Streamlit prototype for AI-assisted plant-health screening. It keeps the Streamlit-first architecture and includes high-contrast button text, image validation, ranked predictions, browser-camera auto-analysis, upload fallback, and configurable server-side ESP32-CAM capture.

## Run locally

Use Python 3.11 or 3.12 if possible, especially for PyTorch compatibility.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

The first model load downloads weights from Hugging Face and can take several minutes depending on the connection. The app defaults to a higher-capacity Vision Transformer (`kimcomehome/plantvillage-vit-leaf-disease`) and lets you switch to the smaller existing MobileNetV2 (`Kathir56/plant-disease-tamilnadu`) if memory or startup time is a problem. You can set `AGRISCAN_MODEL_ID` as an environment variable to add/select a custom compatible Transformers image-classification model.

## Deploy to the existing Streamlit Community Cloud app

1. Replace the repository's entire `app.py` with this file.
2. Ensure `requirements.txt` contains the dependencies in this project. Commit and push to GitHub.
3. Wait for Streamlit Community Cloud to install/restart the app.
4. Test uploads, browser camera, and model inference on the deployed app.
5. If the larger ViT exceeds available memory or times out, switch to MobileNetV2 in the model selector.

The CSS specifically overrides the nested label text inside Streamlit's primary buttons; simply setting a button's outer `color` is not sufficient when global paragraph rules use `!important`.

## ESP32-CAM integration

The app assumes a configurable status path (default `/status`) and capture path (default `/capture`). The status endpoint should return HTTP 2xx when ready; the capture endpoint must return a valid image response. These are example defaults, not confirmed firmware routes.

**Network limitation:** Streamlit Community Cloud runs on a remote server and cannot directly reach a private IP on your home Wi-Fi. For the first integration, run Streamlit locally on the laptop or Raspberry Pi that shares the same LAN as the ESP32-CAM, or use a secure bridge/API reachable by the hosted app. Do not expose an unauthenticated camera to the public internet.

## Model and validation notes

The Vision Transformer is a higher-capacity candidate, not a guarantee of superior field performance. Published results on PlantVillage are dataset-specific; they do not establish accuracy on real farm photographs or Tamil Nadu field conditions. This app labels model scores as model output, not calibrated probabilities. Test both models on the same labelled set of varied images and record correct/incorrect predictions before making any performance claim.
