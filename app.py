import io
import hashlib
import zipfile
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, UnidentifiedImageError
from pillow_heif import register_heif_opener

register_heif_opener()

st.set_page_config(
    page_title="Image Processing Portal",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SUPPORTED = ["jpg", "jpeg", "png", "webp", "heic", "heif", "bmp", "gif", "tif", "tiff"]

# -----------------------------
# Helpers
# -----------------------------
def open_image(uploaded_file):
    uploaded_file.seek(0)
    img = Image.open(uploaded_file)
    try:
        img.seek(0)  # first frame for GIF/animated formats
    except Exception:
        pass
    img = ImageOps.exif_transpose(img)
    return img.copy()

def remove_background(img):
    """Use rembg if installed. It returns an RGBA image."""
    try:
        from rembg import remove
    except ImportError:
        raise RuntimeError(
            "Background removal requires the 'rembg' package. "
            "Install it with: py -m pip install rembg"
        )
    result = remove(img.convert("RGBA"))
    return result.convert("RGBA")

def white_background(img):
    """Composite transparency onto white."""
    rgba = img.convert("RGBA")
    bg = Image.new("RGBA", rgba.size, "white")
    bg.alpha_composite(rgba)
    return bg.convert("RGB")

def fit_resize(img, width, height, mode):
    if mode == "Exact size":
        return img.resize((width, height), Image.Resampling.LANCZOS)
    if mode == "Fit inside":
        return ImageOps.contain(img, (width, height), Image.Resampling.LANCZOS)
    return ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)

def reduce_by_max_dimension(img, max_dimension):
    w, h = img.size
    largest = max(w, h)
    if largest <= max_dimension:
        return img
    scale = max_dimension / largest
    return img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)

def encode_image(img, fmt, quality, progressive=True):
    output = io.BytesIO()
    if fmt == "JPG":
        rgb = white_background(img) if img.mode in ("RGBA", "LA") else img.convert("RGB")
        rgb.save(output, format="JPEG", quality=quality, optimize=True, progressive=progressive)
        return output.getvalue(), "image/jpeg", ".jpg"
    if fmt == "PNG":
        img.save(output, format="PNG", optimize=True)
        return output.getvalue(), "image/png", ".png"
    if fmt == "WEBP":
        img.save(output, format="WEBP", quality=quality, method=6)
        return output.getvalue(), "image/webp", ".webp"
    raise ValueError("Unsupported output format")

def unique_name(name, used):
    base = Path(name).stem
    ext = Path(name).suffix
    candidate = name
    n = 2
    while candidate.lower() in used:
        candidate = f"{base}_{n}{ext}"
        n += 1
    used.add(candidate.lower())
    return candidate

def sha256(data):
    return hashlib.sha256(data).hexdigest()

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("🛠️ Image Tools")
st.sidebar.caption("Choose a tool or use All-in-One.")

tool = st.sidebar.radio(
    "Select Tool",
    [
        "✨ All-in-One",
        "🔄 Convert to JPG",
        "✂️ Remove Background",
        "⬜ White Background",
        "🗜️ Image Compression",
        "📐 Resize / Size Reduce",
        "🏷️ Bulk Rename",
        "🧹 Remove Duplicates",
    ],
)

st.sidebar.divider()
st.sidebar.info(
    "Supported input: JPG, JPEG, PNG, WEBP, HEIC/HEIF, BMP, GIF and TIFF."
)

st.title("🖼️ Image Processing Portal")
st.caption("Bulk image conversion, background tools, compression, resizing, renaming and duplicate cleanup.")

files = st.file_uploader(
    "📤 Upload multiple images",
    type=SUPPORTED,
    accept_multiple_files=True,
    help="You can select many images at once.",
)

# -----------------------------
# Settings
# -----------------------------
with st.sidebar.expander("⚙️ General Settings", expanded=True):
    output_format = st.selectbox("Output format", ["JPG", "PNG", "WEBP"], index=0)
    quality = st.slider("Image quality", 10, 100, 95, 5)
    keep_name = st.checkbox("Keep original filename", True)

with st.sidebar.expander("📐 Resize Settings"):
    resize_mode = st.selectbox("Resize mode", ["No resize", "Exact size", "Fit inside", "Fill / crop"])
    resize_w = st.number_input("Width (px)", min_value=1, value=1000, step=10)
    resize_h = st.number_input("Height (px)", min_value=1, value=1000, step=10)
    max_dimension = st.number_input("Max dimension (px)", min_value=100, value=2000, step=100)

with st.sidebar.expander("🏷️ Rename Settings"):
    rename_prefix = st.text_input("Prefix", value="")
    rename_start = st.number_input("Starting number", min_value=1, value=1, step=1)
    rename_digits = st.slider("Number of digits", 1, 8, 5)
    rename_use_original = st.checkbox("Use original filename + prefix", False)

# -----------------------------
# Processing configuration
# -----------------------------
def process_image(file, index):
    original_name = file.name
    img = open_image(file)

    # Tool-specific processing
    if tool == "🔄 Convert to JPG":
        pass

    elif tool == "✂️ Remove Background":
        img = remove_background(img)

    elif tool == "⬜ White Background":
        # For normal photos, first try to remove the background so the
        # subject is placed on white. This requires rembg.
        if img.mode not in ("RGBA", "LA") and "transparency" not in img.info:
            img = remove_background(img)
        img = white_background(img)

    elif tool == "🗜️ Image Compression":
        pass

    elif tool == "📐 Resize / Size Reduce":
        pass

    elif tool == "🏷️ Bulk Rename":
        pass

    elif tool == "🧹 Remove Duplicates":
        pass

    elif tool == "✨ All-in-One":
        # All-in-One settings are shown below and handled separately.
        pass

    # All-in-One settings
    if tool == "✨ All-in-One":
        if aio_remove_bg:
            img = remove_background(img)
        if aio_white_bg:
            img = white_background(img)

        if aio_resize_mode == "Exact size":
            img = fit_resize(img, aio_w, aio_h, "Exact size")
        elif aio_resize_mode == "Fit inside":
            img = fit_resize(img, aio_w, aio_h, "Fit inside")
        elif aio_resize_mode == "Fill / crop":
            img = fit_resize(img, aio_w, aio_h, "Fill / crop")
        elif aio_resize_mode == "Max dimension":
            img = reduce_by_max_dimension(img, aio_max_dim)

        if aio_brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(aio_brightness)
        if aio_contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(aio_contrast)

    elif tool == "📐 Resize / Size Reduce":
        if resize_mode == "Exact size":
            img = fit_resize(img, resize_w, resize_h, "Exact size")
        elif resize_mode == "Fit inside":
            img = fit_resize(img, resize_w, resize_h, "Fit inside")
        elif resize_mode == "Fill / crop":
            img = fit_resize(img, resize_w, resize_h, "Fill / crop")
        elif resize_mode == "No resize":
            # Optional max dimension still reduces oversized images.
            img = reduce_by_max_dimension(img, max_dimension)

    # Output format
    result_format = output_format
    if tool in ("🔄 Convert to JPG", "✂️ Remove Background", "⬜ White Background",
                "🗜️ Image Compression", "📐 Resize / Size Reduce", "🏷️ Bulk Rename",
                "🧹 Remove Duplicates"):
        result_format = "JPG" if tool != "🗜️ Image Compression" else output_format

    # If removing background, PNG/WebP can preserve transparency.
    # Default JPG intentionally creates white background.
    data, mime, ext = encode_image(img, result_format, quality)

    # Naming
    if tool == "🏷️ Bulk Rename":
        number = int(rename_start) + index
        if rename_use_original:
            stem = Path(original_name).stem
            base = f"{rename_prefix}{stem}_{number:0{rename_digits}d}"
        else:
            base = f"{rename_prefix}{number:0{rename_digits}d}"
        final_name = base + ext
    else:
        stem = Path(original_name).stem if keep_name else f"image_{index+1:05d}"
        final_name = stem + ext

    return {
        "original": original_name,
        "name": final_name,
        "bytes": data,
        "mime": mime,
        "size_before": file.size,
        "size_after": len(data),
        "dimensions": img.size,
    }

# -----------------------------
# All-in-One controls
# -----------------------------
aio_remove_bg = False
aio_white_bg = False
aio_resize_mode = "No resize"
aio_w = 1000
aio_h = 1000
aio_max_dim = 2000
aio_brightness = 1.0
aio_contrast = 1.0

if tool == "✨ All-in-One":
    st.subheader("✨ All-in-One Processing")
    c1, c2, c3 = st.columns(3)
    with c1:
        aio_remove_bg = st.checkbox("✂️ Remove background")
        aio_white_bg = st.checkbox("⬜ White background")
    with c2:
        aio_resize_mode = st.selectbox(
            "Resize",
            ["No resize", "Exact size", "Fit inside", "Fill / crop", "Max dimension"],
        )
        aio_w = st.number_input("Width", 1, 10000, 1000, 10)
        aio_h = st.number_input("Height", 1, 10000, 1000, 10)
    with c3:
        aio_max_dim = st.number_input("Max dimension", 100, 20000, 2000, 100)
        aio_brightness = st.slider("Brightness", 0.5, 1.5, 1.0, 0.05)
        aio_contrast = st.slider("Contrast", 0.5, 1.5, 1.0, 0.05)

    st.write(
        "The All-in-One tool can combine background removal, white background, "
        "resize, brightness/contrast, compression and output-format conversion."
    )

# -----------------------------
# Run
# -----------------------------
if files:
    st.divider()

    if tool == "🧹 Remove Duplicates":
        hashes = {}
        unique_files = []
        duplicate_files = []

        for f in files:
            data = f.getvalue()
            h = sha256(data)
            if h in hashes:
                duplicate_files.append(f.name)
            else:
                hashes[h] = f.name
                unique_files.append(f)

        st.info(f"Found {len(duplicate_files)} duplicate file(s). {len(unique_files)} unique file(s) remain.")

        if duplicate_files:
            with st.expander("Duplicate files"):
                for name in duplicate_files:
                    st.write(name)

        # Convert unique images to JPG for a useful cleaned output.
        work_files = unique_files
    else:
        work_files = files

    converted = []
    errors = []

    progress = st.progress(0)
    status = st.empty()

    for i, file in enumerate(work_files):
        status.write(f"Processing {i+1}/{len(work_files)}: **{file.name}**")
        try:
            converted.append(process_image(file, i))
        except Exception as e:
            errors.append((file.name, str(e)))
        progress.progress((i + 1) / len(work_files))

    progress.empty()
    status.empty()

    if errors:
        st.warning(f"{len(errors)} file(s) could not be processed.")
        with st.expander("Show errors"):
            for name, error in errors:
                st.write(f"**{name}** — {error}")

    if converted:
        # Resolve duplicate output filenames.
        used = set()
        for item in converted:
            item["name"] = unique_name(item["name"], used)

        total_before = sum(x["size_before"] for x in converted)
        total_after = sum(x["size_after"] for x in converted)
        saved = max(0, total_before - total_after)
        saving_pct = (saved / total_before * 100) if total_before else 0

        a, b, c, d = st.columns(4)
        a.metric("Images processed", len(converted))
        b.metric("Original size", f"{total_before / 1024 / 1024:.2f} MB")
        c.metric("Output size", f"{total_after / 1024 / 1024:.2f} MB")
        d.metric("Size saved", f"{saving_pct:.1f}%")

        # Bulk ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in converted:
                zf.writestr(item["name"], item["bytes"])
        zip_buffer.seek(0)

        st.download_button(
            "📦 Download All Images (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="processed_images.zip",
            mime="application/zip",
            use_container_width=True,
        )

        st.divider()
        st.subheader("Processed Images")

        cols = st.columns(3)
        for i, item in enumerate(converted):
            with cols[i % 3]:
                st.image(item["bytes"], caption=item["name"], width=240)
                st.caption(
                    f"{item['dimensions'][0]} × {item['dimensions'][1]} px  |  "
                    f"{item['size_after']/1024:.1f} KB"
                )
                st.download_button(
                    "⬇️ Download",
                    data=item["bytes"],
                    file_name=item["name"],
                    mime=item["mime"],
                    key=f"download_{i}_{item['name']}",
                    use_container_width=True,
                )
else:
    st.info("👆 Upload multiple images to start processing.")
