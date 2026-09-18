# Image Processing Portal

A Streamlit portal for bulk product/image processing.

## Tools in the sidebar

1. All-in-One
2. Convert to JPG
3. Remove Background
4. White Background
5. Image Compression
6. Resize / Size Reduce
7. Bulk Rename
8. Remove Duplicates

## Supported input formats

JPG, JPEG, PNG, WEBP, HEIC, HEIF, BMP, GIF, TIFF

## Run on Windows

Open Command Prompt in this folder and run:

    py -m pip install -r requirements.txt
    py -m streamlit run app.py

Then open the Local URL shown by Streamlit.

## Important: Background removal

Background removal uses the `rembg` AI package. Its first use can download an AI model.
If your Python version does not have a compatible ONNX Runtime build, background removal
may require using a supported Python version (commonly Python 3.11/3.12).

The other tools do not depend on the background-removal model.

## Main features

- Bulk upload
- Convert to JPG
- Remove background
- White background
- JPG/PNG/WEBP output
- Image compression with quality control
- Exact resize
- Fit-inside resize
- Fill/crop resize
- Maximum-dimension size reduction
- Brightness and contrast controls in All-in-One
- Bulk rename with prefix/sequence
- Duplicate detection using SHA-256
- Preview
- Individual download
- ZIP bulk download
- Before/after size statistics
