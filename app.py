import os, io, zipfile, cv2, gc, shutil, hashlib, numpy as np
from PIL import Image
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from rembg import remove, new_session
from datetime import datetime

# 👑 頂層狀態機初始化最前置防線：一開機立刻強制寫入記憶體
if "user_authenticated" not in st.session_state: st.session_state.user_authenticated = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "uploader_key_token" not in st.session_state: st.session_state.uploader_key_token = 1000
if "preview_thumbs" not in st.session_state: st.session_state.preview_thumbs = []
if "temp_ready" not in st.session_state: st.session_state.temp_ready = False

# 👑 Firebase 雲端保險箱初始化
if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except: pass
db = firestore.client() if firebase_admin._apps else None

@st.cache_resource
def load_rembg_session():
    return new_session("silueta")

def get_remote_ip():
    try:
        ctx = st.context if hasattr(st, "context") else None
        if ctx and hasattr(ctx, "headers"):
            if "X-Forwarded-For" in ctx.headers: return ctx.headers["X-Forwarded-For"].split(",")[0].strip()
            elif "X-Real-IP" in ctx.headers: return ctx.headers["X-Real-IP"].strip()
    except: pass
    return "127.0.0.1"

# 👑 航太級輕量化本地語系（徹底根除龐大字典造成的傳輸溢出死穴！）
L = {
    "title": "🌐 網拍電商商品照片 智慧置中裁剪 SaaS",
    "param_header": "⚙️ 圖檔比例容量參數設定",
    "ratio_lbl": "主體佔畫面比例 (10-99%):",
    "size_lbl": "照片檔最大容量限制 (MB):",
    "drag_lbl": "📥 將圖片或整個資料夾拖曳至此（原檔名導出流）",
    "clear_btn": "🗑 清除重選",
    "btn_lbl": "🚀 一鍵快速導出完美置中商品照片",
    "dl_btn": "🎁 點擊下載完美置中相片壓縮包 (ZIP)"
}

st.set_page_config(page_title="NEXUS CROP", page_icon="🌐", layout="wide")
visitor_ip = get_remote_ip()
current_date_str = datetime.now().strftime("%Y-%m-%d")
current_month_str = datetime.now().strftime("%Y-%m")

guest_used_day, guest_used_month = 0, 0
if db and not st.session_state.user_authenticated and visitor_ip != "127.0.0.1":
    try:
        ip_data = db.collection("guest_ips").document(visitor_ip).get().to_dict()
        if ip_data:
            if ip_data.get("last_date") == current_date_str: guest_used_day = ip_data.get("day_used", 0)
            if ip_data.get("last_month") == current_month_str: guest_used_month = ip_data.get("month_used", 0)
    except: pass

current_remaining_quota = min(10 - guest_used_day, 30 - guest_used_month) if not st.session_state.user_authenticated else 50

main_col, side_col = st.columns([0.72, 0.28], gap="large")

with side_col:
    st.markdown("### 📊 NEXUS CROP 會員錢包")
    st.info(f"🕒 免註冊 IP 試用錢包：\n* 今日已用：**{guest_used_day} / 10** Credits\n* 剩餘可用：**{max(0, current_remaining_quota)} 張**")

with main_col:
    st.title(L["title"])
    st.write("---")
    st.markdown(f"#### {L['param_header']}")
    col_p1, col_p2 = st.columns(2)
    with col_p1: ratio = float(st.text_input(L["ratio_lbl"], value="90")) / 100.0
    with col_p2: t_mb = float(st.text_input(L["size_lbl"], value="2.0"))
    
    uploaded_files = st.file_uploader(L["drag_lbl"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"uploader_{st.session_state.uploader_key_token}")
    num_uploaded = len(uploaded_files) if uploaded_files else 0
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(L["clear_btn"], use_container_width=True):
            st.session_state.uploader_key_token += 1
            st.session_state.temp_ready = False
            st.session_state.preview_thumbs = []
            st.rerun()
    with col_btn2:
        start_btn = st.button(L["btn_lbl"], type="primary", use_container_width=True, disabled=(num_uploaded == 0 or num_uploaded > current_remaining_quota))

    zip_path = "/tmp/processed_centered_images.zip"

    if uploaded_files and start_btn:
        saved = 0
        progress_bar = st.progress(0)
        session = load_rembg_session()
        temp_out_dir = "/tmp/processed_centered_images"
        if os.path.exists(temp_out_dir): shutil.rmtree(temp_out_dir)
        if os.path.exists(zip_path): os.remove(zip_path)
        os.makedirs(temp_out_dir, exist_ok=True)
        
        st.session_state.preview_thumbs = [] # 🎯 清空舊預覽
        
        for idx, file in enumerate(uploaded_files, 1):
            try:
                file_raw_name = file.name
                file.seek(0)
                img = cv2.imdecode(np.frombuffer(file.read(), dtype=np.uint8), cv2.IMREAD_COLOR)
                if img is None: continue
                h, w, _ = img.shape
                
                # 👑 100% 純血去重防線
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                output_pil = remove(Image.fromarray(img_rgb), session=session)
                alpha = cv2.cvtColor(np.array(output_pil), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                _, thresh = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                valid_boxes = []
                for c in contours:
                    hull = cv2.convexHull(c)
                    if cv2.contourArea(hull) > (w * h * 0.015):
                        bx, by, bw, bh = cv2.boundingRect(hull)
                        # 🎯 補貼過來的去重熔斷內核
                        roi = img[by:by+bh, bx:bx+bw]
                        if roi.size > 0:
                            s_pil = remove(Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)), session=session)
                            s_alpha = cv2.cvtColor(np.array(s_pil), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                            _, s_thresh = cv2.threshold(s_alpha, 10, 255, cv2.THRESH_BINARY)
                            s_cnt, _ = cv2.findContours(s_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                            if s_cnt:
                                sbx, sby, sbw, sbh = cv2.boundingRect(max(s_cnt, key=cv2.contourArea))
                                if sbw * sbh < (bw * bh * 0.92):
                                    valid_boxes.append((bx + sbx, by + sby, sbw, sbh))
                                    continue
                        valid_boxes.append((bx, by, bw, bh))
                if not valid_boxes: valid_boxes.append((int(w*0.25), int(h*0.25), int(w*0.5), int(w*0.5)))
                
                for part_idx, (bx, by, bw, bh) in enumerate(valid_boxes, 1):
                    cx, cy = bx + bw // 2, by + bh // 2
                    pad_l = min(cx - bw // 2, int((bw / ratio - bw) / 2))
                    pad_r = min((w - cx) - bw // 2, int((bw / ratio - bw) / 2))
                    pad_t = min(cy - bh // 2, int((bh / ratio - bh) / 2))
                    pad_b = min((h - cy) - bh // 2, int((bh / ratio - bh) / 2))
                    
                    cropped = img[cy-bh//2-pad_t : cy+bh//2+pad_b, cx-bw//2-pad_l : cx+bw//2+pad_r]
                    if cropped.size == 0: continue
                    
                    # 👑 秒級就地生成 50KB 超輕量快取縮圖
                    _, thumb_buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, 40])
                    st.session_state.preview_thumbs.append((file_raw_name, thumb_buf.tobytes()))
                    
                    _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    out_name = f"{os.path.splitext(file_raw_name)[0]}_裁切_{part_idx}.jpg" if len(valid_boxes) > 1 else file_raw_name
                    with open(os.path.join(temp_out_dir, out_name), "wb") as f_out: f_out.write(buf.tobytes())
                    saved += 1
            except: pass
            progress_bar.progress(idx / num_uploaded)
            
        if saved > 0:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, _, files in os.walk(temp_out_dir):
                    for f in files: zip_file.write(os.path.join(root, f), f)
            st.session_state.temp_ready = True
            st.rerun()

    # 🔓 🔓 🔓 【持久化安全放行閘門：在 Rerun 外層強勢渲染！】 🔓 🔓 🔓
    if st.session_state.temp_ready and os.path.exists(zip_path):
        with open(zip_path, "rb") as f_zip: zip_data = f_zip.read()
        if st.download_button(label=L["dl_btn"], data=zip_data, file_name="processed_images.zip", mime="application/zip", use_container_width=True):
            if db and visitor_ip != "127.0.0.1":
                db.collection("guest_ips").document(visitor_ip).set({"day_used": guest_used_day + num_uploaded, "month_used": guest_used_month + num_uploaded, "last_date": current_date_str, "last_month": current_month_str})
            st.session_state.uploader_key_token += 1
            st.session_state.temp_ready = False
            st.session_state.preview_thumbs = []
            st.rerun()
            
        # 🎨 🎨 🎨 【震撼亮起：網頁實時大圖預覽網格看板！】 🎨 🎨 🎨
        if st.session_state.preview_thumbs:
            st.write("---")
            st.markdown("### 🎨 AI 完美置中成果實時預覽網格")
            grid_cols = st.columns(4)
            for t_idx, (t_name, t_bytes) in enumerate(st.session_state.preview_thumbs):
                with grid_cols[t_idx % 4]:
                    st.image(t_bytes, use_container_width=True)
                    st.caption(f"📁 {t_name}")
