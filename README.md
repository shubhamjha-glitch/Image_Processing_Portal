# Image Processing Portal — Final Fast Version

White Background is fast and does NOT use AI. Remove Background uses the lightweight u2netp model, caches the model, and reduces very large images during AI processing.

Install:
py -m pip install -r requirements.txt

Run:
py -m streamlit run app.py

If rembg/ONNX does not support your Python version, use Python 3.11 or 3.12 for AI background removal. Other tools do not need the AI model.
