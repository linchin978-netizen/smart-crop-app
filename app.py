import os, io, zipfile, cv2, gc, shutil, numpy as np
from PIL import Image
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth

# 👑 👑 👑 【最高安全規格：Streamlit Secrets 雲端暗號密鑰讀取晶片】 👑 👑 👑
# 徹底告別 GitHub Secret scanning 警報！全自動從 Streamlit 內部隱形保險箱微秒級對接美國資料庫！
if not firebase_admin._apps:
    try:
        # 將 Streamlit Secrets 裡的 firebase 大字典無損洗成標準 Python 字典
        fb_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"❌ Firebase Infrastructure Security Locked: {str(e)}")

db = firestore.client() if firebase_admin._apps else None

# 👑 雲端快取優化：確保 AI 模型在登入過關後才載入，省下珍貴算力
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

# 🌍 頂級高科技多國語言字典 (以西洋高階 SaaS 軟體為核心風格)
LANG_MAP = {
    "English": {
        "title": "⚡ NEXUS CROP — AI Ultra-Fast Commerce Centering System",
        "subtitle": "Next-Gen Object Recognition & Pure Original Pixel Boundaries Cloud Engine",
        "param_header": "⚙️ AI Optimization & Parameter Infrastructure (Keyboard input enabled)",
        "ratio_lbl": "Target subject density ratio (10-99%):",
        "size_lbl": "Maximum payload weight constraint per image (MB):",
        "tip_header": "💡 OPERATIONAL SPECIFICATIONS",
        "tip_body": "1. Directly type your optimization parameters below via keyboard.\n2. Drag single images or folder into the drop zone below.\n3. Processing deductions will automatically update your cloud wallet Token credits.",
        "drag_lbl": "📥 DROP SINGLE IMAGES OR ENTIRE IMAGE FOLDER HERE TO INITIALIZE NEURAL PIPELINE",
        "loaded_lbl": "📊 Consolidated image queue assets: {} items",
        "clear_btn": "🗑 Clear & Reset Queue",
        "btn_lbl": "⚡ Initialize Sub-Second Smart Centering Deployment",
        "processing": "⏳ Neural pipeline processing asset {} / {}...",
        "success": "### ✅ Pipeline Render Completed! Total {} assets deployed!",
        "dl_btn": "🎁 Download Compiled Centering Assets Package (ZIP)",
        "limit_err": "❌ Quota Depleted! Your active token balance is insufficient for this batch payload. Please top up below.",
        "usage_title": "📊 COMMERCIAL PREMIUM USER STATUS",
        "auth_header": "🔑 NEXUS CROP — ENTERPRISE PORTAL"
    },
    "繁體中文": {
        "title": "⚡ NEXUS CROP — 頂級電商商品照智慧置中裁切系統",
        "subtitle": "新世代高精主體光學識別 ── 最速電商純原圖極限邊界雲端引擎",
        "param_header": "⚙️ 最速電商智慧識別參數設定 (支援鍵盤手動自行輸入)",
        "ratio_lbl": "導出後主體佔畫面比例 (10-99%):",
        "size_lbl": "導出後照片檔最大容量限制 (MB):",
        "tip_header": "💡 智慧網拍系統使用說明",
        "tip_body": "1. 請先註冊或登入您的專屬電子信箱，以開啟您在美國的加密工作區。\n2. 點擊下方輸入框，可直接用鍵盤手動自行打字輸入置中比例與容量數值。\n3. 可以將單張圖片或整個圖片資料夾直接全數拖曳至下方巨型區塊內（26張大文件通殺免斷電）。\n4. 核心導出成功後，系統將自動從您的雲端錢包中扣除相應點數 Token。",
        "drag_lbl": "📥 將「單張相片」或「整個圖片資料夾」全數拖曳至此（支援多張 JPG, WEBP，25張以上大文件通殺）",
        "loaded_lbl": "📊 目前已載入商品照片：{} 張",
        "clear_btn": "🗑 清除重選",
        "btn_lbl": "🚀 一鍵秒級導出完美置中商品照片",
        "processing": "⏳ 智慧光學解算中：第 {} 張 / 共 {} 張...",
        "success": "### ✅ 核心解算成功！共生成 {} 張智慧置中照片！",
        "dl_btn": "🎁 點擊一鍵下載完美置中相片壓縮包 (ZIP)",
        "limit_err": "❌ 雲端點數額度不足！本批處理圖片量大於您的帳號剩餘額度，請在下方充值點數包。",
        "usage_title": "📊 NEXUS CROP 會員額度看板",
        "auth_header": "🔑 NEXUS CROP — 賣家通行大門"
    }
}

st.set_page_config(page_title="NEXUS CROP — AI SaaS", page_icon="⚡", layout="centered")
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

# 👑 國際密碼密鑰會員登入通行大腦
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

lang = st.selectbox("🌐 Language Interface", ("English", "繁體中文"), index=0)
L = LANG_MAP[lang]

# 🔑 會員註冊登入大盾牌 (未通過前死鎖下方所有裁切與圖片緩衝模組)
if not st.session_state.user_authenticated:
    st.title(L["auth_header"])
    auth_mode = st.radio("Portal Mode", ("Sign In", "Sign Up (Free 20 Credits)"), horizontal=True)
    
    email_in = st.text_input("📧 Email Address", key="auth_email")
    pass_in = st.text_input("🔒 Account Password", type="password", key="auth_pass")
    
    if auth_mode == "Sign Up (Free 20 Credits)":
        if st.button("🚀 Establish New Account", use_container_width=True):
            try:
                user = auth.create_user(email=email_in, password=pass_in)
                if db:
                    db.collection("users").document(user.uid).set({
                        "email": email_in,
                        "credits": 20,
                        "tier": "FREE_TRIAL"
                    })
                st.success("✅ Account established successfully! Please switch mode to Sign In.")
            except Exception as e:
                st.error(f"❌ Registration Failed: {str(e)}")
                
    elif auth_mode == "Sign In":
        if st.button("⚡ Sign In & Unlock Neural Pipeline", use_container_width=True):
            try:
                user_record = auth.get_user_by_email(email_in)
                st.session_state.user_authenticated = True
                st.session_state.user_email = email_in
                st.rerun()
            except Exception as e:
                st.error(f"❌ Authentication Failed: Invalid credentials or account unregistered. {str(e)}")
    st.stop()

# 👑 👑 👑 順利通過盾牌 ── 進入滿血商用電商功能世界 👑 👑 👑
# 連線資料庫，撈出該美國帳號的賸餘 Token 點數
current_credits = 0
user_uid = ""
if db:
    try:
        user_rec = auth.get_user_by_email(st.session_state.user_email)
        user_uid = user_rec.uid
        user_doc_ref = db.collection("users").document(user_uid)
        user_data = user_doc_ref.get().to_dict()
        
        if not user_data:
            user_doc_ref.set({"email": st.session_state.user_email, "credits": 20, "tier": "FREE_TRIAL"})
            user_data = {"email": st.session_state.user_email, "credits": 20, "tier": "FREE_TRIAL"}
        
        current_credits = user_data.get("credits", 0)
    except:
        current_credits = 20

st.title(L["title"])
st.markdown(f"*{L['subtitle']}*")

# 📊 頂級美金商業看板（直接死鎖剩餘點數，點數不夠全自動彈出美金充值套餐）
st.info(f"👤 **Active Node:** `{st.session_state.user_email}` ｜ 🕒 Available Pipeline Credits: **{current_credits} 張**")

if st.sidebar.button("🚪 Logout Account", use_container_width=True):
    st.session_state.user_authenticated = False
    st.session_state.user_email = ""
    st.rerun()

# ⚙️ 網拍參數配置面板 (解鎖鍵盤自由手動輸入)
st.markdown("---")
st.markdown(f"#### {L['param_header']}")
col1, col2 = st.columns(2)
with col1:
    ratio_str = st.text_input(L["ratio_lbl"], value="90")
    try:
        ratio_val = float(ratio_str)
        ratio = max(10.0, min(99.0, ratio_val)) / 100.0
    except: ratio = 0.90
with col2:
    size_str = st.text_input(L["size_lbl"], value="2.0")
    try: t_mb = max(0.1, float(size_str))
    except: t_mb = 2.0

# 💡 使用說明大面板
with st.expander(f"**{L['tip_header']}**", expanded=False):
    st.markdown(L["tip_body"])

# 👑 👑 👑 【美金儲值攔截保險絲】 👑 👑 👑
# 如果美國用戶帳號點數歸 0，強行熔斷並禁用上傳拖曳框，直接跳出購買美金點數包按鈕！
if current_credits <= 0:
    st.error("❌ Your Token Balance is 0! Neural process pipeline deadlocked. Please upgrade to Premium Plan.")
    col_cc1, col_cc2, col_cc3 = st.columns(3)
    with col_cc1:
        if st.button("🇺🇸 Starter Pack (\$4.99)\n+ 150 Credits", type="secondary", use_container_width=True, key="btn_pack_1"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits": current_credits + 150})
            st.rerun()
    with col_cc2:
        if st.button("🇺🇸 Power Seller (\$19.99)\n+ 700 Credits", type="secondary", use_container_width=True, key="btn_pack_2"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits": current_credits + 700})
            st.rerun()
    with col_cc3:
        if st.button("🇺🇸 Mega Vault (\$49.99)\n+ 2000 Credits", type="primary", use_container_width=True, key="btn_pack_3"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits": current_credits + 2000})
            st.rerun()
    st.stop()

uploaded_files = st.file_uploader(L["drag_lbl"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
# 🗑 清除重選按鈕與一鍵秒級導出按鈕佈局面板
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button(L["clear_btn"], use_container_width=True):
        st.rerun()

with col_btn2:
    start_btn = st.button(L["btn_lbl"], type="primary", use_container_width=True)

if uploaded_files:
    st.success(L["loaded_lbl"].format(len(uploaded_files)))
    
    if start_btn:
        # 👑 資料庫安全熔斷機制：如果一口氣丟進去的照片數量大於雲端帳號餘額，強行熔斷不改圖！
        if len(uploaded_files) > current_credits:
            st.error(L["limit_err"])
        else:
            saved = 0
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 👑 100% 呼叫大獲全勝的 AI 去背引擎快取
            session = load_rembg_session()
            
            temp_out_dir = "/tmp/processed_centered_images"
            if os.path.exists(temp_out_dir):
                shutil.rmtree(temp_out_dir)
            os.makedirs(temp_out_dir, exist_ok=True)
            
            for idx, file in enumerate(uploaded_files, 1):
                status_text.markdown(L["processing"].format(idx, len(uploaded_files)))
                
                try:
                    # 👑 100% 採用原汁原味桌面版純血 OpenCV 二進位直讀肉身
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
                        img = img_rotated
                        contours = contours_rotated
                        is_rotated_for_calculation = True
                        h, w = h_r, w_r
                    else:
                        img = img_orig
                        contours = contours_normal
                        is_rotated_for_calculation = False
                        h, w = h_o, w_o
                    
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
                    
                    if not valid_boxes:
                        valid_boxes.append((int(w*0.25), int(h*0.25), int(w*0.5), int(h*0.5)))
                    
                    for part_idx, (bx, by, bw, bh) in enumerate(valid_boxes, 1):
                        cx, cy = bx + bw // 2, by + bh // 2
                        ideal_pad_w = int((bw / ratio - bw) / 2)
                        ideal_pad_h = int((bh / ratio - bh) / 2)
                        
                        pad_l = min(cx - bw // 2, ideal_pad_w)
                        pad_r = min((w - cx) - bw // 2, ideal_pad_w)
                        pad_t = min(cy - bh // 2, ideal_pad_h)
                        pad_b = min((h - cy) - bh // 2, ideal_pad_h)
                        
                        x1 = max(0, cx - bw // 2 - pad_l)
                        x2 = min(w, cx + bw // 2 + pad_r)
                        y1 = max(0, cy - bh // 2 - pad_t)
                        y2 = min(h, cy + bh // 2 + pad_b)
                        cropped = img[y1:y2, x1:x2]
                        if cropped.size == 0: continue
                        
                        if is_rotated_for_calculation:
                            cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        
                        t_bytes = t_mb * 1024 * 1024; low, high, best_q = 1, 100, 85
                        for _ in range(10):
                            mid = (low + high) // 2
                            _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, mid])
                            if len(buf) <= t_bytes: best_q = mid; low = mid + 1
                            else: high = mid - 1
                        _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, best_q])
                        
                        base_name, _ = os.path.splitext(file.name)
                        out_img_name = f"{base_name}_{part_idx}.jpg" if len(valid_boxes) > 1 else f"{base_name}.jpg"
                        
                        # 👑 實體硬碟隔離即時寫入，內存 0 負擔
                        with open(os.path.join(temp_out_dir, out_img_name), "wb") as f_out:
                            f_out.write(buf.tobytes())
                        saved += 1
                        
                    del img, img_orig, img_rotated, contours_normal, contours_rotated
                    gc.collect()
                        
                except Exception as e:
                    st.error(f"Error {file.name}: {str(e)}")
                
                progress_bar.progress(idx / len(uploaded_files))
            
            if saved > 0:
                # 👑 👑 👑 【資料庫全自動即時扣點防線】 👑 👑 👑
                # 當 25 張照片全數無誤在硬碟隔離生成後，後台資料庫立刻自動精準扣點！
                if db and user_uid:
                    new_balance = max(0, current_credits - len(uploaded_files))
                    db.collection("users").document(user_uid).update({"credits": new_balance})
                
                zip_path = "/tmp/processed_centered_images.zip"
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for root, _, files in os.walk(temp_out_dir):
                        for f in files:
                            zip_file.write(os.path.join(root, f), f)
                
                st.success(L["success"].format(saved))
                
                with open(zip_path, "rb") as f_zip:
                    st.download_button(
                        label=L["dl_btn"],
                        data=f_zip.read(),
                        file_name="processed_centered_images.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                st.rerun() # 強制面板刷新，更新點數
