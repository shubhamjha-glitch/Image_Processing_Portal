import io, zipfile, hashlib
from pathlib import Path
import streamlit as st
from PIL import Image, ImageOps, ImageEnhance
from pillow_heif import register_heif_opener

register_heif_opener()
st.set_page_config(page_title="Image Processing Portal", page_icon="🖼️", layout="wide")
SUPPORTED=["jpg","jpeg","png","webp","heic","heif","bmp","gif","tif","tiff"]

@st.cache_resource(show_spinner=False)
def get_rembg_session():
    from rembg import new_session
    return new_session("u2netp")

def open_image(f):
    f.seek(0)
    with Image.open(f) as im:
        try: im.seek(0)
        except Exception: pass
        return ImageOps.exif_transpose(im).copy()

def remove_background(img):
    try:
        from rembg import remove
    except ImportError:
        raise RuntimeError("Run: py -m pip install rembg")
    original=img.size
    max_side=1400
    if max(original)>max_side:
        s=max_side/max(original)
        work=img.convert("RGBA").resize((max(1,int(original[0]*s)),max(1,int(original[1]*s))),Image.Resampling.LANCZOS)
    else:
        work=img.convert("RGBA")
    out=remove(work,session=get_rembg_session()).convert("RGBA")
    return out.resize(original,Image.Resampling.LANCZOS) if out.size!=original else out

def white_background(img):
    rgba=img.convert("RGBA")
    bg=Image.new("RGBA",rgba.size,"white")
    bg.alpha_composite(rgba)
    return bg.convert("RGB")

def resize_image(img,mode,w,h,max_dim):
    if mode=="Exact size": return img.resize((w,h),Image.Resampling.LANCZOS)
    if mode=="Fit inside": return ImageOps.contain(img,(w,h),Image.Resampling.LANCZOS)
    if mode=="Fill / crop": return ImageOps.fit(img,(w,h),Image.Resampling.LANCZOS)
    if mode=="Max dimension" and max(img.size)>max_dim:
        s=max_dim/max(img.size)
        return img.resize((max(1,int(img.width*s)),max(1,int(img.height*s))),Image.Resampling.LANCZOS)
    return img

def encode(img,fmt,q):
    out=io.BytesIO()
    if fmt=="JPG":
        white_background(img).save(out,"JPEG",quality=q,optimize=True,progressive=True)
        return out.getvalue(),"image/jpeg",".jpg"
    if fmt=="PNG":
        img.save(out,"PNG",optimize=True); return out.getvalue(),"image/png",".png"
    img.save(out,"WEBP",quality=q,method=6); return out.getvalue(),"image/webp",".webp"

def unique_name(name,used):
    p=Path(name); x=name; n=2
    while x.lower() in used:
        x=f"{p.stem}_{n}{p.suffix}"; n+=1
    used.add(x.lower()); return x

def process(f,i,tool,output_format,quality,keep_name,resize_mode,resize_w,resize_h,max_dimension,
            prefix,start_no,digits,original_plus,aio_remove,aio_white,aio_resize,aio_w,aio_h,aio_max,aio_brightness,aio_contrast):
    img=open_image(f)
    if tool=="✂️ Remove Background" or (tool=="✨ All-in-One" and aio_remove): img=remove_background(img)
    if tool=="⬜ White Background" or (tool=="✨ All-in-One" and aio_white): img=white_background(img)
    if tool=="📐 Resize / Size Reduce": img=resize_image(img,resize_mode,resize_w,resize_h,max_dimension)
    elif tool=="✨ All-in-One":
        img=resize_image(img,aio_resize,aio_w,aio_h,aio_max)
        if aio_brightness!=1: img=ImageEnhance.Brightness(img).enhance(aio_brightness)
        if aio_contrast!=1: img=ImageEnhance.Contrast(img).enhance(aio_contrast)
    fmt=output_format
    if tool in ["🔄 Convert to JPG","✂️ Remove Background","⬜ White Background","🏷️ Bulk Rename","🧹 Remove Duplicates"]: fmt="JPG"
    data,mime,ext=encode(img,fmt,quality)
    if tool=="🏷️ Bulk Rename":
        num=int(start_no)+i
        name=(f"{prefix}{Path(f.name).stem}_{num:0{digits}d}" if original_plus else f"{prefix}{num:0{digits}d}")+ext
    else:
        name=f"{Path(f.name).stem if keep_name else f'image_{i+1:05d}'}{ext}"
    return {"name":name,"bytes":data,"mime":mime,"before":f.size,"after":len(data),"dim":img.size}

st.sidebar.title("🛠️ Image Tools")
tool=st.sidebar.radio("Select Tool",["✨ All-in-One","🔄 Convert to JPG","✂️ Remove Background","⬜ White Background","🗜️ Image Compression","📐 Resize / Size Reduce","🏷️ Bulk Rename","🧹 Remove Duplicates"])
st.sidebar.divider()
st.sidebar.success("⚡ White Background is FAST — no AI.")
st.sidebar.caption("✂️ Remove Background uses lightweight u2netp AI; first run can take longer.")

with st.sidebar.expander("⚙️ Output Settings",expanded=True):
    output_format=st.selectbox("Output format",["JPG","PNG","WEBP"])
    quality=st.slider("Quality",10,100,90,5)
    keep_name=st.checkbox("Keep original filename",True)
with st.sidebar.expander("📐 Resize Settings"):
    resize_mode=st.selectbox("Resize mode",["No resize","Exact size","Fit inside","Fill / crop","Max dimension"])
    resize_w=st.number_input("Width",1,10000,1000,10)
    resize_h=st.number_input("Height",1,10000,1000,10)
    max_dimension=st.number_input("Max dimension",100,20000,2000,100)
with st.sidebar.expander("🏷️ Rename Settings"):
    prefix=st.text_input("Prefix","")
    start_no=st.number_input("Starting number",1,999999,1,1)
    digits=st.slider("Digits",1,8,5)
    original_plus=st.checkbox("Original filename + number",False)

st.title("🖼️ Image Processing Portal")
st.caption("Bulk conversion, background tools, compression, resizing, renaming and duplicate cleanup.")
files=st.file_uploader("📤 Upload multiple images",type=SUPPORTED,accept_multiple_files=True)

aio_remove=aio_white=False
aio_resize="No resize"; aio_w=aio_h=1000; aio_max=2000; aio_brightness=aio_contrast=1.0
if tool=="✨ All-in-One":
    st.subheader("✨ All-in-One")
    c1,c2,c3=st.columns(3)
    with c1:
        aio_remove=st.checkbox("✂️ Remove Background")
        aio_white=st.checkbox("⬜ White Background")
    with c2:
        aio_resize=st.selectbox("Resize",["No resize","Exact size","Fit inside","Fill / crop","Max dimension"])
        aio_w=st.number_input("Width",1,10000,1000,10); aio_h=st.number_input("Height",1,10000,1000,10)
    with c3:
        aio_max=st.number_input("Max dimension",100,20000,2000,100)
        aio_brightness=st.slider("Brightness",0.5,1.5,1.0,0.05)
        aio_contrast=st.slider("Contrast",0.5,1.5,1.0,0.05)
    st.info("White Background only flattens transparency. It does not run AI.")

if files:
    work=files
    if tool=="🧹 Remove Duplicates":
        seen=set(); work=[]; dup=[]
        for f in files:
            h=hashlib.sha256(f.getvalue()).hexdigest()
            if h in seen: dup.append(f.name)
            else: seen.add(h); work.append(f)
        st.info(f"{len(work)} unique image(s), {len(dup)} duplicate(s) detected.")
    results=[]; errors=[]
    progress=st.progress(0); status=st.empty()
    for i,f in enumerate(work):
        status.write(f"Processing {i+1}/{len(work)}: **{f.name}**")
        try:
            results.append(process(f,i,tool,output_format,quality,keep_name,resize_mode,resize_w,resize_h,max_dimension,prefix,start_no,digits,original_plus,aio_remove,aio_white,aio_resize,aio_w,aio_h,aio_max,aio_brightness,aio_contrast))
        except Exception as e: errors.append((f.name,str(e)))
        progress.progress((i+1)/len(work))
    progress.empty(); status.empty()
    if errors:
        st.warning(f"{len(errors)} file(s) failed.")
        with st.expander("Show errors"):
            for n,e in errors: st.write(f"**{n}** — {e}")
    if results:
        used=set()
        for r in results: r["name"]=unique_name(r["name"],used)
        before=sum(r["before"] for r in results); after=sum(r["after"] for r in results)
        a,b,c,d=st.columns(4); a.metric("Processed",len(results)); b.metric("Original",f"{before/1048576:.2f} MB"); c.metric("Output",f"{after/1048576:.2f} MB"); d.metric("Saved",f"{max(0,before-after)/before*100 if before else 0:.1f}%")
        z=io.BytesIO()
        with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as zz:
            for r in results: zz.writestr(r["name"],r["bytes"])
        st.download_button("📦 Download All Images (ZIP)",z.getvalue(),"processed_images.zip","application/zip",use_container_width=True)
        st.divider(); st.subheader("Processed Images")
        cols=st.columns(3)
        for i,r in enumerate(results):
            with cols[i%3]:
                st.image(r["bytes"],caption=r["name"],width=240)
                st.caption(f"{r['dim'][0]} × {r['dim'][1]} px | {r['after']/1024:.1f} KB")
                st.download_button("⬇️ Download",r["bytes"],r["name"],r["mime"],key=f"dl_{i}",use_container_width=True)
else:
    st.info("👆 Upload multiple images to start.")
