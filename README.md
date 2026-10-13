# Agriscan AI — Streamlit edition

A dark forest / pastel sage Streamlit prototype for AI-assisted plant-health screening. Keeps the original Transformers model and adds a high-contrast interface, image validation, ranked predictions, honest score interpretation, browser camera auto-analysis, upload fallback, and a configurable server-side ESP32-CAM capture path.

## Run locally

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

First model load can take time, because Transformers downloads the model weights. If using Python 3.13 or a platform without a compatible PyTorch wheel, use a supported Python version such as 3.11 or 3.12.

## Deploy to the existing Streamlit Community Cloud app

1. Replace the existing repository's `app.py` with this `app.py`.
2. Ensure the repository's `requirements.txt` includes the packages in this project. Commit and push to GitHub.
3. Wait for Streamlit Community Cloud to install and restart the app.
4. Test upload, browser camera, model inference, and errors.

Keep `.streamlit/config.toml` if you want the dark theme to be consistent. The CSS in `app.py` is also responsible for the glass-like surfaces and explicit contrast.

## ESP32-CAM integration

The app assumes a configurable status path (default `/status`) and capture path (default `/capture`). The status endpoint should return HTTP 2xx when ready; the capture endpoint must return a valid image response. These are defaults, not confirmed firmware routes.

**Important network limitation:** a Streamlit Community Cloud server cannot directly reach a private IP address on your home Wi-Fi. For the first prototype, run Streamlit locally on the same LAN as the ESP32-CAM, or create a secure bridge/API reachable by the hosted Streamlit server. Do not expose an unauthenticated camera to the public internet.

## Model notes

Default model ID: `Kathir56/plant-disease-tamilnadu`. The model score is not a calibrated probability, and field accuracy has not been established by this demo. Validate a varied, labelled test set before making accuracy claims.
