# Agriscan AI UI upgrade notes

## Design intent
Preserve deep forest green, pastel sage, glass-like surfaces, rounded corners and restrained botanical motion. Change composition rather than piling on more widgets: a split editorial hero, focused scan area, and compact feature cards.

## Functional additions
- Heuristic capture-quality check (brightness, grayscale contrast, resolution).
- Optional side-by-side comparison against the other configured classifier.
- Exportable JSON result report.
- Session-only field notebook with CSV export.
- Optional field note attached to the scan report.

## Important limitations
- The field notebook is in Streamlit session state; it is not a persistent database.
- Quality score is a transparent heuristic, not model confidence or disease detection.
- Model comparison can be slow due to model download/loading and is not a ground-truth test.
- No change here proves real-field accuracy or ESP32-CAM connectivity.
