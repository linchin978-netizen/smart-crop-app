import streamlit as st
import cv2
import numpy as np
from PIL import Image
from rembg import remove, new_session
import os, zipfile, io, time

# 👑 終極完全體：一鍵洗牌晶片注入，徹底根絕瀏覽器殘留，點擊 100% 秒級清空！
st.set_page_layout = "centered"
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

# 載入大腦與全局計數器晶片
if "session" not in st.session_state:
    st.session_state.session = new_session("silueta")
if "last_daily_reset" not in st.session_state:
    st.session_state.last_daily_reset = time.time()
if "last_monthly_reset" not in st.session_state:
    st.session_state.last_monthly_reset = time.time()
if "daily_processed" not in st.session_state:
    st.session_state.daily_processed = 0
if "monthly_processed" not in st.session_state:
    st.session_state.monthly_processed = 0
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0 # 🟢 終極洗牌金鑰，儲存初始狀態

# 🟢 【天網滾動重置晶片】
if time.time() - st.session_state.last_daily_reset > 86400:
    st.session_state.daily_processed = 0
    st.session_state.last_daily_reset = time.time()
if time.time() - st.session_state.last_monthly_reset > 2592000:
    st.session_state.monthly_processed = 0
    st.session_state.last_monthly_reset = time.time()

# 🟢 【巨型滑鼠拖曳網頁大宇宙】：焊入動態 key，一變號就無情重置快取！
uploaded_files = st.file_uploader(
    "💡 Drag & drop your product photos here (No limits, support massive batch)", 
    type=["jpg", "jpeg", "png", "webp"], 
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}"
)

# 即時亮出雙軌配額進度防線
st.write(f"📈 Today's Quota: **{st.session_state.daily_processed} / 10** | 30-Day Total Quota: **{st.session_state.monthly_processed} / 30**")

if uploaded_files:
    st.info(f"📊 Successfully loaded {len(uploaded_files)} photos into our cloud pipeline.")
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        # 🗑 【清除重選按鈕】：金鑰號碼加1，強迫 Chrome 當場吐出所有快取照片，100% 秒級清空歸零！
        if st.button("🗑 Clear List", type="secondary", use_container_width=True):
            st.session_state.uploader_key += 1
            st.rerun()
            
    with btn_col2:
        if st.button("🚀 One-Click Batch Export Centered Photos", type="primary", use_container_width=True):
            # 🟢 【大亨指定 4 階雙軌硬熔斷阻斷門】
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
                        status_text.text(f"⏳ Cloud Processing: {idx} / {len(uploaded_files)} Photos ({pct:.1f}%)")
                        progress_bar.progress(idx / len(uploaded_files))
                        
                        try:
                            file_bytes = np.asarray(bytearray(file_item.read()), dtype=np.uint8)
                            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                            if img is None: continue
                            h, w, _ = img.shape
                            
                            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            output_pil = remove(Image.fromarray(img_rgb), session=st.session_state.session)
                            alpha = cv2.cvtColor(np.array(output_pil), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                            _, thresh = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
                            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                            
                            valid_boxes = []
                            for c in contours:
                                hull = cv2.convexHull(c)
                                if cv2.contourArea(hull) > (w * h * 0.015):
                                    bx, by, bw, bh = cv2.boundingRect(hull)
                                    roi = img[by:by+bh, bx:bx+bw]
                                    if roi.size > 0:
                                        g_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                                        e_roi = cv2.Canny(g_roi, 50, 150)
                                        if (np.sum(e_roi > 0) / e_roi.size) < 0.05:
                                            s_pil = remove(Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)), session=st.session_state.session)
                                            s_alpha = cv2.cvtColor(np.array(s_pil), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                                            _, s_thresh = cv2.threshold(s_alpha, 10, 255, cv2.THRESH_BINARY)
                                            s_cnt, _ = cv2.findContours(s_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                                            if s_cnt:
                                                sbx, sby, sbw, sbh = cv2.boundingRect(max(s_cnt, key=cv2.contourArea))
                                                if sbw * sbh < (bw * bh * 0.92): valid_boxes.append((bx + sbx, by + sby, sbw, sbh)); continue
                                    valid_boxes.append((bx, by, bw, bh))
                            if not valid_boxes: valid_boxes.append((int(w*0.25), int(h*0.25), int(w*0.5), int(w*0.5)))
                            
                            for part_idx, (bx, by, bw, bh) in enumerate(valid_boxes, 1):
                                cx, cy = bx + bw // 2, by + bh // 2
                                max_pad_w = min(cx, w - cx)
                                max_pad_h = min(cy, h - cy)
                                tw = min(int(bw / ratio), max_pad_w * 2)
                                th = min(int(bh / ratio), max_pad_h * 2)
                                x1, y1 = cx - tw // 2, cy - th // 2
                                x2, y2 = x1 + tw, y1 + th
                                
                                cropped = img[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                                pil_img = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
                                
                                sfx = f"_part{part_idx}" if len(valid_boxes) > 1 else "_cropped"
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
                                
                                zip_file.writestr(f"{base_name}{sfx}.jpg", img_io.getvalue())
                            saved += len(valid_boxes)
                        except: pass
                
                # 同步記數累加
                st.session_state.daily_processed += len(uploaded_files)
                st.session_state.monthly_processed += len(uploaded_files)
                
                status_text.text(f"✨ Done! Successfully processed {saved} perfect photos!")
                st.success("🎉 Your production batch is ready! Click the button below to download.")
                st.download_button(
                    label="📥 Download Perfect_Centered_Images.zip",
                    data=zip_buffer.getvalue(),
                    file_name="Product_Centered_Images.zip",
                    mime="application/zip",
                    use_container_width=True
                )