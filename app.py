import streamlit as st
import cv2
import numpy as np
from PIL import Image
import os, zipfile, io, time

# 👑 4層定價漏斗網頁完全體，代碼不落地、0套件衝突，100% 根絕死白閃退！
st.set_page_config(page_title="Smart Crop Master", layout="centered")
st.title("🌐 Smart Subject Recognition & Auto-Center Crop")
st.subheader("Enterprise E-commerce Photo Pipeline (SaaS Core)")

# 4層定價展示與成本平攤話術
st.markdown("""
### 💰 Choose Your Production Power
* **FREE TRIAL**: $0/mo (Limit: 10 pics/Day, Max 30 pics/30 Days) - *Test our rounding-protection power.*
* **STARTER TIER**: $29/mo (Limit: 900 pics per 30 Days) - *For small active retail stores.*
* **PROFESSIONAL TIER**: $99/mo (Limit: 4,500 pics per 30 Days) - **Under $0.02 USD per perfect photo!**
* **ENTERPRISE VIP**: $1,999 Lifetime (100% Unlimited Forever) - *For global card & retail giants.*
""")

st.write("---")

# 📊 網頁參數設定列
col1, col2 = st.columns(2)
with col1:
    ratio = st.number_input("Subject Ratio in Image (10-99%):", min_value=10, max_value=99, value=90) / 100.0
with col2:
    t_mb = st.number_input("Max File Size Limit (MB):", min_value=1.0, max_value=10.0, value=2.0)

# 載入全局時間與計數器
if "last_daily_reset" not in st.session_state: st.session_state.last_daily_reset = time.time()
if "last_monthly_reset" not in st.session_state: st.session_state.last_monthly_reset = time.time()
if "daily_processed" not in st.session_state: st.session_state.daily_processed = 0
if "monthly_processed" not in st.session_state: st.session_state.monthly_processed = 0
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0

# 【天網滾動重置晶片】
if time.time() - st.session_state.last_daily_reset > 86400:
    st.session_state.daily_processed = 0
    st.session_state.last_daily_reset = time.time()
if time.time() - st.session_state.last_monthly_reset > 2592000:
    st.session_state.monthly_processed = 0
    st.session_state.last_monthly_reset = time.time()

# 🟢 【巨型滑鼠拖曳網頁大宇宙】
uploaded_files = st.file_uploader(
    "💡 Drag & drop your product photos here (No limits, support massive batch)", 
    type=["jpg", "jpeg", "png", "webp"], 
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}"
)

st.write(f"📈 Today's Quota: **{st.session_state.daily_processed} / 10** | 30-Day Total Quota: **{st.session_state.monthly_processed} / 30**")

if uploaded_files:
    st.info(f"📊 Successfully loaded {len(uploaded_files)} photos into our cloud pipeline.")
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🗑 Clear List", type="secondary", use_container_width=True):
            st.session_state.uploader_key += 1
            st.rerun()
            
    with btn_col2:
        if st.button("🚀 One-Click Batch Export Centered Photos", type="primary", use_container_width=True):
            # 🟢 【天網雙軌限額攔截】
            if st.session_state.daily_processed >= 10 or (st.session_state.daily_processed + len(uploaded_files)) > 10:
                st.error("❌ Daily Quota Exceeded! Your limit is 10 photos per 24H. Come back tomorrow or upgrade to unlock full production power!")
            elif st.session_state.monthly_processed >= 30 or (st.session_state.monthly_processed + len(uploaded_files)) > 30:
                st.error("❌ 30-Day Maximum Limit Reached! You have used up the maximum 30 free trial photos within this rolling cycle. Please upgrade to Pro ($99/mo) or Enterprise ($1,999 Lifetime) now!")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    saved = 0
                    for idx, file_item in enumerate(uploaded_files, 1):
                        pct = (idx / len(uploaded_files)) * 100
                        status_text.text(f"⏳ Processing Photo: {idx} / {len(uploaded_files)} ({pct:.1f}%)")
                        progress_bar.progress(idx / len(uploaded_files))
                        
                        try:
                            file_bytes = np.asarray(bytearray(file_item.read()), dtype=np.uint8)
                            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                            if img is None: continue
                            h, w, _ = img.shape
                            
                            # 👑 大亨特化自適應影像幾何對齊（安全防線兜底）
                            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                            
                            valid_boxes = []
                            for c in contours:
                                hull = cv2.convexHull(c)
                                if cv2.contourArea(hull) > (w * h * 0.015):
                                    valid_boxes.append(cv2.boundingRect(hull))
                            if not valid_boxes: valid_boxes.append((int(w*0.05), int(h*0.05), int(w*0.9), int(h*0.9)))
                            
                            bx, by, bw, bh = max(valid_boxes, key=lambda b: b * b)
                            cx, cy = bx + bw // 2, by + bh // 2
                            max_pad_w = min(cx, w - cx)
                            max_pad_h = min(cy, h - cy)
                            tw = min(int(bw / ratio), max_pad_w * 2)
                            th = min(int(bh / ratio), max_pad_h * 2)
                            x1, y1 = cx - tw // 2, cy - th // 2
                            x2, y2 = x1 + tw, y1 + th
                            
                            cropped = img[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                            pil_img = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
                            
                            base_name = os.path.splitext(file_item.name)
                            img_io = io.BytesIO()
                            t_bytes = t_mb * 1024 * 1024
                            low, high, best_q = 1, 100, 85
                            for _ in range(10):
                                mid = (low + high) // 2
                                img_io.seek(0); img_io.truncate(0)
                                pil_img.save(img_io, "JPEG", quality=mid)
                                if img_io.tell() <= t_bytes: best_q = mid; low = mid + 1
                                else: high = mid - 1
                            img_io.seek(0); img_io.truncate(0)
                            pil_img.save(img_io, "JPEG", quality=best_q)
                            
                            zip_file.writestr(f"{base_name}_cropped.jpg", img_io.getvalue())
                            saved += 1
                        except: pass
                        
                st.session_state.daily_processed += len(uploaded_files)
                st.session_state.monthly_processed += len(uploaded_files)
                
                status_text.text(f"✨ Done! Successfully processed {saved} product photos!")
                st.success("🎉 Your production batch is ready! Click the button below to download.")
                st.download_button(
                    label="📥 Download Perfect_Centered_Images.zip",
                    data=zip_buffer.getvalue(),
                    file_name="Product_Centered_Images.zip",
                    mime="application/zip",
                    use_container_width=True
                )
