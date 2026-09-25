import os, io, zipfile, cv2, gc, shutil, numpy as np
from PIL import Image
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth

# 👑 Firebase 雲端保險箱最高資安初始化連線晶片 (從 Streamlit Secrets 保險箱讀取暗號)
if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        pass

db = firestore.client() if firebase_admin._apps else None

# 👑 雲端快取優化：確保 AI 去背模型在雲端唯一下載一次，節省效能開銷
@st.cache_resource
def load_rembg_session():
    from rembg import new_session
    return new_session("silueta")

def get_ai_bounding_boxes(cv_img, session):
    from rembg import remove
    img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    output_pil = remove(Image.fromarray(img_rgb), session=session)
    alpha = cv2.cvtColor(np.array(output_pil), cv2.COLOR_RGBA2BGRA)[:, :, 3]
    _, thresh = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

# 🌍 頂級高科技 PLG 產品字典 (完美融合 4 層定價話術與費用計算)
LANG_MAP = {
    "English": {
        "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
        "subtitle": "Enterprise E-commerce Photo Pipeline (Standby)",
        "param_header": "⚙️ AI Optimization & Parameter Infrastructure (Keyboard input enabled)",
        "ratio_lbl": "Target subject density ratio (10-99%):",
        "size_lbl": "Maximum payload weight constraint per image (MB):",
        "tip_header": "💡 FREE OPERATIONAL SPECIFICATIONS",
        "tip_body": "1. Directly type your optimization parameters below via keyboard.\n2. Drag single images or folder into the drop zone below.\n3. Click the primary button to initialize the neural render pipeline for FREE!\n4. Unlock your cloud wallet package to download the processed ZIP payload.",
        "drag_lbl": "📥 DROP SINGLE IMAGES OR ENTIRE IMAGE FOLDER HERE FOR FREE NEURAL CENTERING",
        "loaded_lbl": "📊 Consolidated image queue assets: {} items",
        "clear_btn": "🗑 Clear & Reset Queue",
        "btn_lbl": "🚀 One-Click Batch Export Centered Photos",
        "processing": "⏳ Neural pipeline processing asset {} / {}...",
        "success": "### ✅ Pipeline Render Completed! Total {} assets compiled in cloud disk!",
        "dl_btn": "🎁 Unlock & Download Centering Assets Package (ZIP)",
        "limit_err": "🔒 DEPLOYMENT PACK LOCKED ── Processed assets are ready! Please sign in or purchase token packages below to unlock and download your compiled high-res ZIP package immediately.",
        "usage_title": "📊 PREMIUM WORKSPACE WALLET",
        "welcome": "👋 Welcome, Premium Partner: **{}** ｜ 🪙 Wallet Balance: **{} Credits**"
    },
    "繁體中文": {
        "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
        "subtitle": "Enterprise E-commerce Photo Pipeline (Standby)",
        "param_header": "⚙️ 最速電商智慧識別參數設定 (支援鍵盤手動自行輸入)",
        "ratio_lbl": "導出後主體佔畫面比例 (10-99%):",
        "size_lbl": "導出後照片檔最大容量限制 (MB):",
        "tip_header": "💡 商品智慧置中系統說明 (免費開放體驗中)",
        "tip_body": "1. 點擊下方輸入框，可直接用鍵盤手動自行打字輸入置中比例數值。\n2. 可以將「單張網拍圖片」或「整個卡片資料夾」直接全數拖曳至下方巨型向量場中。\n3. 按下秒級導出按鈕即可全自動免費解算！\n4. 畫面顯示成功生成後，登入您的雲端錢包或充值點數包即可立刻帶走高畫質相片包！",
        "drag_lbl": "📥 將「單張相片」或「整個圖片資料夾」全數拖曳至此（免註冊直接免費體驗，25張大文件通殺）",
        "loaded_lbl": "📊 目前已載入商品照片：{} 張",
        "clear_btn": "🗑 清除重選",
        "btn_lbl": "🚀 One-Click Batch Export Centered Photos",
        "processing": "⏳ 智慧光學解算中：第 {} 張 / 共 {} 張...",
        "success": "### ✅ 核心解算成功！共生成 {} 張智慧置中照片！",
        "dl_btn": "🎁 點擊解鎖並下載完美置中相片壓縮包 (ZIP)",
        "limit_err": "🔒 相片打包已安全鎖死 ── 免註冊試用額度（每天限 10 張 / 每月限 30 張）已用完！請在右側註冊/登入，或充值點數套餐，即可立刻全速下載您改好的高畫質 ZIP 壓縮檔！",
        "usage_title": "📊 NEXUS CROP 會員錢包看板",
        "welcome": "👋 歡迎回來，尊貴的電商夥伴：**{}** ｜ 🪙 專屬錢包餘額：**{} 點 Token**"
    }
}

st.set_page_config(page_title="NEXUS CROP — AI SaaS", page_icon="🌐", layout="wide")

# 👑 巨型拖曳方框 CSS 注入晶片
st.markdown("""
    <style>
    [data-testid="stFileUploader"] { padding: 25px 0px; }
    [data-testid="stFileUploaderDropzone"] {
        padding: 60px 20px !important;
        border: 2px dashed #3498db !important;
        border-radius: 12px !important;
        background-color: #f8fafc !important;
        transition: all 0.3s ease-in-out;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #2980b9 !important;
        background-color: #f1f5f9 !important;
        box-shadow: 0px 4px 20px rgba(52, 152, 219, 0.15);
    }
    </style>
""", unsafe_allow_html=True)
# 👑 👑 👑 【免註冊智慧計數狀態機 ── 初始化安全晶片】 👑 👑 👑
# 讓陌生訪客不用註冊，也能在背景紀錄他今天用了幾張，確保 10/24H 防禦不被白嫖
if "daily_usage" not in st.session_state:
    st.session_state.daily_usage = 0
if "monthly_usage" not in st.session_state:
    st.session_state.monthly_usage = 0

# 👑 國際密碼密鑰會員狀態機
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

lang = st.selectbox("🌐 Language Interface", ("English", "繁體中文"), index=0)
L = LANG_MAP[lang]

# 👑 全球高級電商雙欄位大氣佈局：左邊放無阻礙核心功能，右邊放 Firebase 會員控制與充值看板
main_col, side_col = st.columns([5, 2], gap="large")

with side_col:
    st.markdown(f"### {L['usage_title']}")
    if not st.session_state.user_authenticated:
        # 📊 免註冊用戶，右側即時秀出他今天剩幾張免費額度，拉高焦慮感促使註冊！
        st.info(f"🕒 Unregistered Free Tier:\n* Daily Used: **{st.session_state.daily_usage} / 10** pics\n* Monthly Used: **{st.session_state.monthly_usage} / 30** pics")
        st.markdown("---")
        auth_mode = st.radio("Portal Access", ("Sign In", "Sign Up (Free 20)"), horizontal=True)
        email_in = st.text_input("📧 Email")
        pass_in = st.text_input("🔒 Password", type="password")
        if auth_mode == "Sign Up (Free 20)":
            if st.button("🚀 Establish Account", use_container_width=True):
                try:
                    user = auth.create_user(email=email_in, password=pass_in)
                    if db: db.collection("users").document(user.uid).set({"email": email_in, "credits": 20, "tier": "FREE_TRIAL"})
                    st.success("✅ Account established! Switch to Sign In.")
                except Exception as e: st.error(f"❌ Failed: {str(e)}")
        else:
            if st.button("⚡ Access Account", use_container_width=True):
                try:
                    user_record = auth.get_user_by_email(email_in)
                    st.session_state.user_authenticated = True
                    st.session_state.user_email = email_in
                    st.rerun()
                except Exception as e: st.error(f"❌ Failed: {str(e)}")
    else:
        # 同步 Firebase 雲端真實資料庫點數
        current_credits = 0
        user_uid = ""
        if db:
            try:
                user_rec = auth.get_user_by_email(st.session_state.user_email)
                user_uid = user_rec.uid
                user_doc_ref = db.collection("users").document(user_uid)
                user_data = user_doc_ref.get().to_dict()
                current_credits = user_data.get("credits", 0)
            except: current_credits = 0
        st.success(L["welcome"].format(st.session_state.user_email, current_credits))
        
        # 🪙 美金儲值點數包
        st.markdown("---")
        st.markdown("#### 🪙 Top Up Cloud Wallet")
        if st.button("🇺🇸 Starter Pack (\$4.99) ── +150 Credits", use_container_width=True):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits": current_credits + 150})
            st.rerun()
        if st.button("🇺🇸 Power Seller (\$19.99) ── +700 Credits", use_container_width=True):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits": current_credits + 700})
            st.rerun()
        if st.button("🇺🇸 Mega Vault (\$49.99) ── +2000 Credits", use_container_width=True, type="primary"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits": current_credits + 2000})
            st.rerun()
            
        if st.button("🚪 Sign Out Workspace", use_container_width=True):
            st.session_state.user_authenticated = False
            st.session_state.user_email = ""
            st.rerun()

with main_col:
    # 👑 100% 灌入您指定的頂級高端歐美 SaaS 標題與「4層定價平攤話術」風格文字
    st.title(L["title"])
    st.markdown(f"### *{L['subtitle']}*")
    
    st.markdown("""
    ### 💰 Choose Your Production Power
    * **FREE TRIAL**: $0/mo (Limit: 10 pics/24H) - *Test our rounding-protection power.*
    * **STARTER TIER**: $29/mo (Limit: 30 pics/day) - *For small active retail stores.*
    * **PROFESSIONAL TIER**: $99/mo (Limit: 150 pics/day) - **Under $0.02 USD per perfect photo!**
    * **ENTERPRISE VIP**: $1,999 Lifetime (100% Unlimited Forever) - *For global card & retail giants.*
    """)
    
    st.write("---")
    st.markdown(f"#### {L['param_header']}")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        ratio_str = st.text_input("Subject Ratio in Image (10-99%):", value="90")
        try: ratio = max(10.0, min(99.0, float(ratio_str))) / 100.0
        except: ratio = 0.90
    with col_p2:
        size_str = st.text_input("Max File Size Limit (MB):", value="2.0")
        try: t_mb = max(0.1, float(size_str))
        except: t_mb = 2.0

    uploaded_files = st.file_uploader(L["drag_lbl"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(L["clear_btn"], use_container_width=True):
            st.rerun()
    with col_btn2:
        start_btn = st.button(L["btn_lbl"], type="primary", use_container_width=True)

    if uploaded_files:
        st.success(L["loaded_lbl"].format(len(uploaded_files)))
        
        # 👑 大方放行，允許任何陌生人在實體硬碟直接試用跑進度條！
        if start_btn:
            saved = 0
            progress_bar = st.progress(0)
            status_text = st.empty()
            session = load_rembg_session()
            
            temp_out_dir = "/tmp/processed_centered_images"
            if os.path.exists(temp_out_dir): shutil.rmtree(temp_out_dir)
            os.makedirs(temp_out_dir, exist_ok=True)
            
            for idx, file in enumerate(uploaded_files, 1):
                status_text.markdown(L["processing"].format(idx, len(uploaded_files)))
                try:
                    file_bytes = np.frombuffer(file.read(), dtype=np.uint8)
                    img_orig = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                    if img_orig is None: continue
                    
                    contours_normal = get_ai_bounding_boxes(img_orig, session)
                    img_rotated = cv2.rotate(img_orig, cv2.ROTATE_90_CLOCKWISE)
                    contours_rotated = get_ai_bounding_boxes(img_rotated, session)
                    
                    h_o, w_o, _ = img_orig.shape
                    valid_cnt_normal = sum(1 for c in contours_normal if cv2.contourArea(cv2.convexHull(c)) > (w_o * h_o * 0.015))
                    h_r, w_r, _ = img_rotated.shape
                    valid_cnt_rotated = sum(1 for c in contours_rotated if cv2.contourArea(cv2.convexHull(c)) > (w_r * h_r * 0.015))
                    
                    if valid_cnt_rotated > valid_cnt_normal:
                        img = img_rotated; contours = contours_rotated; is_rotated_for_calculation = True; h, w = h_r, w_r
                    else:
                        img = img_orig; contours = contours_normal; is_rotated_for_calculation = False; h, w = h_o, w_o
                    
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
                                    s_pil = remove(Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)), session=session)
                                    s_alpha = cv2.cvtColor(np.array(s_pil), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                                    _, s_thresh = cv2.threshold(s_alpha, 10, 255, cv2.THRESH_BINARY)
                                    s_cnt, _ = cv2.findContours(s_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                                    if s_cnt:
                                        sbx_p, sby_p, sbw_p, sbh_p = cv2.boundingRect(max(s_cnt, key=cv2.contourArea))
                                        if sbw_p * sbh_p < (bw * bh * 0.92):
                                            valid_boxes.append((bx + sbx_p, by + sby_p, min(bw, sbw_p), min(bh, sbh_p)))
                                            continue
                            valid_boxes.append((bx, by, bw, bh))
                    
                    if not valid_boxes: valid_boxes.append((int(w*0.25), int(h*0.25), int(w*0.5), int(h*0.5)))
                    
                    for part_idx, (bx, by, bw, bh) in enumerate(valid_boxes, 1):
                        cx, cy = bx + bw // 2, by + bh // 2
                        ideal_pad_w = int((bw / ratio - bw) / 2); ideal_pad_h = int((bh / ratio - bh) / 2)
                        pad_l = min(cx - bw // 2, ideal_pad_w); pad_r = min((w - cx) - bw // 2, ideal_pad_w)
                        pad_t = min(cy - bh // 2, ideal_pad_h); pad_b = min((h - cy) - bh // 2, ideal_pad_h)
                        x1 = max(0, cx - bw // 2 - pad_l); x2 = min(w, cx + bw // 2 + pad_r)
                        y1 = max(0, cy - bh // 2 - pad_t); y2 = min(h, cy + bh // 2 + pad_b)
                        cropped = img[y1:y2, x1:x2]
                        if cropped.size == 0: continue
                        if is_rotated_for_calculation: cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        
                        t_bytes = t_mb * 1024 * 1024; low, high, best_q = 1, 100, 85
                        for _ in range(10):
                            mid = (low + high) // 2
                            _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, mid])
                            if len(buf) <= t_bytes: best_q = mid; low = mid + 1
                            else: high = mid - 1
                        _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, best_q])
                        
                        base_name, _ = os.path.splitext(file.name)
                        out_img_name = f"{base_name}_{part_idx}.jpg" if len(valid_boxes) > 1 else f"{base_name}.jpg"
                        with open(os.path.join(temp_out_dir, out_img_name), "wb") as f_out: f_out.write(buf.tobytes())
                        saved += 1
                        
                    del img, img_orig, img_rotated, contours_normal, contours_rotated; gc.collect()
                except Exception as e: st.error(f"Error {file.name}: {str(e)}")
                progress_bar.progress(idx / len(uploaded_files))
            
            if saved > 0:
                st.session_state.compiled_saved = saved
                st.session_state.temp_ready = True
                st.success(L["success"].format(saved))
                
        # 👑 👑 👑 【情感勒索保險絲：點擊一鍵下載時，雙軌判定扣點與免費限額！】 👑 👑 👑
        if "temp_ready" in st.session_state and st.session_state.temp_ready:
            zip_path = "/tmp/processed_centered_images.zip"
            if not os.path.exists(zip_path):
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for root, _, files in os.walk("/tmp/processed_centered_images"):
                        for f in files: zip_file.write(os.path.join(root, f), f)
                        
            user_authed = st.session_state.user_authenticated
            user_credits_val = current_credits if (user_authed and 'current_credits' in locals()) else 0
            
            # 🔒 下載大閘門：如果「未登入」且「免註冊額度超過 10 張/24H or 30張/30天」，直接彈出紅字鎖死按鈕！
            if not user_authed:
                if st.session_state.daily_usage + len(uploaded_files) > 10 or st.session_state.monthly_usage + len(uploaded_files) > 30:
                    st.error(L["limit_err"])
                else:
                    # 免註冊額度足夠，放行下載並扣除免註冊額度！
                    with open(zip_path, "rb") as f_zip:
                        if st.download_button(label=L["dl_btn"], data=f_zip.read(), file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True):
                            st.session_state.daily_usage += len(uploaded_files)
                            st.session_state.monthly_usage += len(uploaded_files)
                            st.session_state.temp_ready = False
                            st.rerun()
            else:
                # 登入會員狀態，改走 Firebase 真實雲端 Token 扣點大腦
                if user_credits_val < len(uploaded_files):
                    st.error(L["limit_err"])
                else:
                    with open(zip_path, "rb") as f_zip:
                        if st.download_button(label=L["dl_btn"], data=f_zip.read(), file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True):
                            new_balance = max(0, user_credits_val - len(uploaded_files))
                            if db and user_uid:
                                db.collection("users").document(user_uid).update({"credits": new_balance})
                            st.session_state.temp_ready = False
                            st.rerun()
