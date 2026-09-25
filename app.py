import os
import io
import zipfile
import cv2
import gc
import shutil
import hashlib
import numpy as np
from PIL import Image
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from rembg import remove, new_session
from datetime import datetime

if "user_authenticated" not in st.session_state: 
    st.session_state.user_authenticated = False
if "user_email" not in st.session_state: 
    st.session_state.user_email = ""
if "uploader_key_token" not in st.session_state: 
    st.session_state.uploader_key_token = 1000
if "temp_ready" not in st.session_state:
    st.session_state.temp_ready = False
    if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except:
        pass

db = firestore.client() if firebase_admin._apps else None

@st.cache_resource
def load_rembg_session():
    return new_session("silueta")

def get_remote_ip():
    try:
        ctx = st.context if hasattr(st, "context") else None
        if ctx and hasattr(ctx, "headers"):
            headers = ctx.headers
            if "X-Forwarded-For" in headers:
                return headers["X-Forwarded-For"].split(",")[0].strip()
            elif "X-Real-IP" in headers:
                return headers["X-Real-IP"].strip()
    except:
        pass
    return "127.0.0.1"

LANG_MAP = {}
LANG_MAP["English"] = {
    "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
    "subtitle": "Trading Card & E-commerce Photo Smart Centering, Batch Splitting, and Weight Control System",
    "pricing_html": "### 💰 Choose Your Production Power\n* **🌟 FREE TRIAL**: **$0** (50 Free Credits)\n* **🪙 STARTER PACK**: **$4.99** (150 Credits)",
    "param_header": "⚙️ Layout Ratio & Capacity Parameters",
    "ratio_lbl": "Target subject density ratio (10-99%):",
    "size_lbl": "Maximum payload weight constraint per image (MB):",
    "drag_lbl": "📥 DROP ENTIRE IMAGE FOLDER HERE",
    "loaded_lbl": "📊 Consolidated image queue assets: {} items",
    "clear_btn": "🗑 Clear & Reset Queue",
    "btn_lbl": "🚀 One-Click Quick Export Centered Photos",
    "processing": "⏳ Neural pipeline processing asset {} / {}...",
    "success": "### ✅ Pipeline Render Completed! Total {} centered photos compiled!",
    "dl_btn": "🎁 Download Centering Assets Package (ZIP)",
    "limit_err": "🔒 Sorry, your anonymous trial quota is exhausted.",
    "dup_err": "⚠️ Duplicate photos detected! Please reset queue.",
    "usage_title": "📊 PREMIUM WORKSPACE WALLET",
    "guest_info": "🕒 Anonymous IP Wallet:\n* Today Used: **{} / 10**\n* 30-Day Used: **{} / 30**\n* 💡 Balance: **{} items**",
    "welcome": "👋 Welcome: **{}** \n* 🪙 Wallet: **{} Credits**\n* 💡 Balance: **{} items**"
}

LANG_MAP["Deutsch"] = {
    "title": "🌐 Intelligente Objekterkennung & Auto-Zentrierter Zuschnitt",
    "subtitle": "E-Commerce- und Sammelkarten-Fotos intelligent zentrieren",
    "pricing_html": "### 💰 Wählen Sie Ihre Produktionsleistung\n* **🌟 TESTVERSION**: **$0** (50 Gratis-Credits)\n* **🪙 STARTER**: **$4.99** (150 Credits)",
    "param_header": "⚙️ Parameter für Layout-Verhältnis & Dateigröße",
    "ratio_lbl": "Ziel-Dichte des Hauptobjekts (10-99%):",
    "size_lbl": "Maximale Dateigrößenbeschränkung pro Bild (MB):",
    "drag_lbl": "📥 ZIEHEN SIE DEN GESAMTEN BILDERORDNER HIERHER",
    "loaded_lbl": "📊 Geladene Medien-Assets: {} Elemente",
    "clear_btn": "🗑 Warteschlange zurücksetzen",
    "btn_lbl": "🚀 Zentrierte Fotos mit einem Klick exportieren",
    "processing": "⏳ Verarbeitung läuft: Bild {} / {}...",
    "success": "### ✅ Verarbeitung abgeschlossen! Insgesamt {} Fotos erstellt!",
    "dl_btn": "🎁 Zentrierte Bilder herunterladen (ZIP)",
    "limit_err": "🔒 Entschuldigung, Ihr anonymes Testguthaben ist aufgebraucht.",
    "dup_err": "⚠️ Doppelte Fotos erkannt! Bitte Warteschlange zurücksetzen.",
    "usage_title": "📊 PREMIUM WORKSPACE WALLET",
    "guest_info": "🕒 Anonymes IP-Guthaben:\n* Heute: **{} / 10**\n* 30-Tage: **{} / 30**\n* 💡 Guthaben: **{} Bilder**",
    "welcome": "👋 Willkommen: **{}** \n* 🪙 Gesamtguthaben: **{} Credits**\n* 💡 Guthaben: **{} Bilder**"
}
LANG_MAP["繁體中文"] = {
    "title": "🌐 網拍電商商品照片 ── 智慧自動置中裁剪系統",
    "subtitle": "卡牌、網拍商品照一鍵自動裁切、主體完美置中、圖檔比例容量自由設定",
    "pricing_html": "### 💰 選擇您的智慧生產力方案\n* **🌟 免費體驗**: **$0** (即送 50 免費點數)\n* **🪙 賣家入門包**: **$4.99** (內含 150 點數)",
    "param_header": "⚙️ 圖檔比例容量參數 (可自訂數值)",
    "ratio_lbl": "導出後主體佔畫面比例 (10-99%):",
    "size_lbl": "導出後照片檔最大容量限制 (MB):",
    "drag_lbl": "📥 將「單張相片」或「整個圖片資料夾」全數拖曳至此（免註冊免費體驗）",
    "loaded_lbl": "📊 目前已載入商品照片：{} 張",
    "clear_btn": "🗑 清除重選",
    "btn_lbl": "🚀 一鍵快速導出完美置中商品照片",
    "processing": "⏳ 智慧光學解算中：第 {} 張 / 共 {} 張...",
    "success": "### ✅ 核心解算成功！共生成 {} 張智慧置中照片！請點選下方下載。",
    "dl_btn": "🎁 點擊下載完美置中相片壓縮包 (ZIP)",
    "limit_err": "🔒 抱歉，您的免註冊試用額度已用完。請在右側註冊登入領取免費點數！",
    "dup_err": "⚠️ 偵測到重複上傳相同照片！請清除重選以防止點數重複扣除爭議！",
    "usage_title": "📊 NEXUS CROP 會員錢包看板",
    "guest_info": "🕒 免註冊 IP 試用錢包：\n* 今日已用額度：**{} / 10** Credits\n* 30日累計使用：**{} / 30** Credits\n* 💡 剩餘可用總張數：**{} 張**",
    "welcome": "👋 歡迎回來，尊貴的電商夥伴：**{}** \n* 🪙 專屬錢包總餘額：**{} Credits**\n* 💡 剩餘可導出總張數：**{} 張**"
}

LANG_MAP["简体中文"] = {
    "title": "🌐 网拍电商商品照片 ── 智慧自动置中裁剪系统",
    "subtitle": "卡牌、网拍商品照一键自动裁切、主体完美置中、图档比例容量自由设定",
    "pricing_html": "### 💰 选择您的智慧生产力方案\n* **🌟 免费体验**: **$0** (即送 50 免费点数)\n* **🪙 卖家入门包**: **$4.99** (内含 150 点数)",
    "param_header": "⚙️ 图档比例容量参数 (可自订数值)",
    "ratio_lbl": "导出后主体占画面比例 (10-99%):",
    "size_lbl": "导出后照片档 maximum 容量限制 (MB):",
    "drag_lbl": "📥 将单张相片 or 整个图片文件夹全数拖拽至此（免注册免费体验）",
    "loaded_lbl": "📊 目前已载入商品照片：{} 张",
    "clear_btn": "🗑 清除重选",
    "btn_lbl": "🚀 一键快速导出完美置中商品照片",
    "processing": "⏳ 智慧光学解算中：第 {} 张 / 共 {} 张...",
    "success": "### ✅ 核心解算成功！共生成 {} 张智慧置中照片！",
    "dl_btn": "🎁 点击下载完美置中相片压缩包 (ZIP)",
    "limit_err": "🔒 抱歉，您的免注册试用额度已用完。欢迎在右侧注册登录！",
    "dup_err": "⚠️ 侦测到重复上传相同照片！请使用清除重选。",
    "usage_title": "📊 NEXUS CROP 会员钱包看板",
    "guest_info": "🕒 免注册 IP 试用钱包：\n* 今日已用：**{} / 10**\n* 30日累计：**{} / 30**\n* 💡 剩余可用：**{} 张**",
    "welcome": "👋 欢迎回来：**{}** \n* 🪙 专属钱包总余额：**{} Credits**\n* 💡 剩余可导出：**{} 张**"
}
LANG_MAP["日本語"] = {
    "title": "🌐 AI 商品画像自動中央配置＆自動クロップシステム",
    "subtitle": "トレカ・EC商品画像の自動クロップ",
    "pricing_html": "### 💰 プランを選択してください\n* **🌟 無料体験**: **$0** (50枚)\n* **🪙 スターター**: **$4.99** (150枚)",
    "param_header": "⚙️ 画像比率とファイル容量パラメータ",
    "ratio_lbl": "出力後の商品主体の表示比率 (10-99%):",
    "size_lbl": "出力画像の最大容量制限 (MB):",
    "drag_lbl": "📥 画像フォルダをここにドラッグ＆ドロップ",
    "loaded_lbl": "📊 読み込まれた画像：{} 枚",
    "clear_btn": "🗑 キューをクリア",
    "btn_lbl": "🚀 ワンクリックで中央配置画像を高速エクスポート",
    "processing": "⏳ 解析中：第 {} 枚 / 全 {} 枚...",
    "success": "### ✅ 解析完了！合計 {} 枚の画像が生成されました！",
    "dl_btn": "🎁 クロップ画像をダウンロード (ZIP)",
    "limit_err": "🔒 無料お試し枠は終了しました。",
    "dup_err": "⚠️ 重複画像が検出されました！",
    "usage_title": "📊 プレミアム会員ウォレット状況",
    "guest_info": "🕒 IPお試し財布:\n* 本日: **{} / 10**\n* 30日間: **{} / 30**\n* 💡 残り利用可能: **{} 枚**",
    "welcome": "👋 お帰りなさい: **{}** \n* 🪙 残高: **{} Credits**\n* 💡 残り利用可能: **{} 枚**"
}

LANG_MAP["Français"] = LANG_MAP["English"]
LANG_MAP["한국어"] = LANG_MAP["English"]
LANG_MAP["Bahasa Melayu"] = LANG_MAP["English"]
LANG_MAP["Bahasa Indonesia"] = LANG_MAP["English"]

lang = st.selectbox("🌐 Language Interface", ("English", "Deutsch", "Français", "繁體中文", "简体中文", "日本語", "한국어", "Bahasa Melayu", "Bahasa Indonesia"), index=3)
L = LANG_MAP[lang]
visitor_ip = get_remote_ip()
current_date_str = datetime.now().strftime("%Y-%m-%d")
current_month_str = datetime.now().strftime("%Y-%m")

guest_used_day = 0
guest_used_month = 0
user_authed = st.session_state.user_authenticated
credits_total = 0
user_uid = ""

if db and not user_authed and visitor_ip != "127.0.0.1":
    try:
        ip_doc_ref = db.collection("guest_ips").document(visitor_ip)
        ip_data = ip_doc_ref.get().to_dict()
        if ip_data:
            if ip_data.get("last_date") == current_date_str:
                guest_used_day = ip_data.get("day_used", 0)
            if ip_data.get("last_month") == current_month_str:
                guest_used_month = ip_data.get("month_used", 0)
    except:
        pass

if not user_authed:
    rem_day = max(0, 10 - guest_used_day)
    rem_month = max(0, 30 - guest_used_month)
    current_remaining_quota = min(rem_day, rem_month)
else:
    if db:
        try:
            user_rec = auth.get_user_by_email(st.session_state.user_email)
            user_uid = user_rec.uid
            user_data = db.collection("users").document(user_uid).get().to_dict()
            credits_total = user_data.get("credits_total", 0)
        except:
            credits_total = 50
    current_remaining_quota = credits_total
    main_col, side_col = st.columns([0.72, 0.28], gap="large")

with side_col:
    st.markdown(f"### {L['usage_title']}")
    if not user_authed:
        st.info(L["guest_info"].format(guest_used_day, guest_used_month, current_remaining_quota))
        st.markdown("---")
        auth_mode = st.radio("Portal Access", ("Sign In", "Sign Up"), horizontal=True)
        email_in = st.text_input("📧 Email", key="auth_email")
        pass_in = st.text_input("🔒 Password", type="password", key="auth_pass")
        if auth_mode == "Sign Up":
            if st.button("🚀 Establish Account", use_container_width=True):
                try:
                    user = auth.create_user(email=email_in, password=pass_in)
                    if db: db.collection("users").document(user.uid).set({"email": email_in, "credits_total": 50})
                    st.success("✅ Success! Switch to Sign In.")
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
        st.success(L["welcome"].format(st.session_state.user_email, credits_total, current_remaining_quota))
        st.markdown("---")
        if st.button("🚪 Sign Out Workspace", use_container_width=True):
            st.session_state.user_authenticated = False
            st.session_state.user_email = ""
            st.session_state.temp_ready = False
            st.rerun()
            with main_col:
    st.title(L["title"])
    st.markdown(f"### *{L['subtitle']}*")
    st.write("---")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        ratio_str = st.text_input(L["ratio_lbl"], value="90", key="crop_ratio")
        try: ratio = max(10.0, min(99.0, float(ratio_str))) / 100.0
        except: ratio = 0.90
    with col_p2:
        size_str = st.text_input(L["size_lbl"], value="2.0", key="file_size_max")
        try: t_mb = max(0.1, float(size_str))
        except: t_mb = 2.0

    uploaded_files = st.file_uploader(L["drag_lbl"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"file_uploader_core_{st.session_state.uploader_key_token}")
    num_uploaded = len(uploaded_files) if uploaded_files else 0
    quota_violation = num_uploaded > current_remaining_quota
    duplicate_violation = False

    if num_uploaded > 0 and not quota_violation:
        seen_hashes = set()
        for f_check in uploaded_files:
            f_check.seek(0)
            file_hash = hashlib.md5(f_check.read()).hexdigest()
            f_check.seek(0)
            if file_hash in seen_hashes: duplicate_violation = True; break
            seen_hashes.add(file_hash)
            
    if quota_violation: st.error(L["limit_err"])
    if duplicate_violation: st.error(L["dup_err"])

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(L["clear_btn"], use_container_width=True):
            st.session_state.uploader_key_token += 1
            st.session_state.temp_ready = False
            st.rerun()
    with col_btn2:
        any_violation = quota_violation or duplicate_violation or (current_remaining_quota <= 0 and num_uploaded == 0)
        start_btn = st.button(L["btn_lbl"], type="primary", use_container_width=True, disabled=any_violation)

    zip_path = "/tmp/processed_centered_images.zip"
    if uploaded_files and not any_violation and start_btn:
        saved = 0
        progress_bar = st.progress(0)
        session = load_rembg_session()
        temp_out_dir = "/tmp/processed_centered_images"
        if os.path.exists(temp_out_dir): shutil.rmtree(temp_out_dir)
        if os.path.exists(zip_path): os.remove(zip_path)
        os.makedirs(temp_out_dir, exist_ok=True)
        
        for idx, file in enumerate(uploaded_files, 1):
            try:
                file_raw_name = getattr(file, "name", "photo.jpg")
                file.seek(0)
                img_orig = cv2.imdecode(np.frombuffer(file.read(), dtype=np.uint8), cv2.IMREAD_COLOR)
                if img_orig is None: continue
                
                output_pil_o = remove(Image.fromarray(cv2.cvtColor(img_orig, cv2.COLOR_BGR2RGB)), session=session)
                alpha_o = cv2.cvtColor(np.array(output_pil_o), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                _, thresh_o = cv2.threshold(alpha_o, 10, 255, cv2.THRESH_BINARY)
                contours_normal, _ = cv2.findContours(thresh_o, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                img_rotated = cv2.rotate(img_orig, cv2.ROTATE_90_CLOCKWISE)
                output_pil_r = remove(Image.fromarray(cv2.cvtColor(img_rotated, cv2.COLOR_BGR2RGB)), session=session)
                alpha_r = cv2.cvtColor(np.array(output_pil_r), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                _, thresh_r = cv2.threshold(alpha_r, 10, 255, cv2.THRESH_BINARY)
                contours_rotated, _ = cv2.findContours(thresh_r, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                h_o, w_o, _ = img_orig.shape
                v_normal = sum(1 for c in contours_normal if cv2.contourArea(cv2.convexHull(c)) > (w_o * h_o * 0.015))
                h_r, w_r, _ = img_rotated.shape
                v_rotated = sum(1 for c in contours_rotated if cv2.contourArea(cv2.convexHull(c)) > (w_r * h_r * 0.015))
                
                if v_rotated > v_normal:
                    img = img_rotated; contours = contours_rotated; is_rotated = True; h, w = h_r, w_r
                else:
                    img = img_orig; contours = contours_normal; is_rotated = False; h, w = h_o, w_o
                
                valid_boxes = []
                for c in contours:
                    hull = cv2.convexHull(c)
                    if cv2.contourArea(hull) > (w * h * 0.015):
                        bx, by, bw, bh = cv2.boundingRect(hull)
                        roi = img[by:by+bh, bx:bx+bw]
                        if roi.size > 0:
                            g_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                            if (np.sum(cv2.Canny(g_roi, 50, 150) > 0) / g_roi.size) < 0.05:
                                s_pil = remove(Image.fromarray(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)), session=session)
                                s_alpha = cv2.cvtColor(np.array(s_pil), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                                _, s_thresh = cv2.threshold(s_alpha, 10, 255, cv2.THRESH_BINARY)
                                s_cnt, _ = cv2.findContours(s_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                                if s_cnt:
                                    sbx, sby, sbw, sbh = cv2.boundingRect(max(s_cnt, key=cv2.contourArea))
                                    if sbw * sbh < (bw * bh * 0.92):
                                        valid_boxes.append((bx + sbx, by + sby, sbw, sbh)); continue
                        valid_boxes.append((bx, by, bw, bh))
                        if not valid_boxes: valid_boxes.append((int(w*0.25), int(h*0.25), int(w*0.5), int(w*0.5)))
                
                for part_idx, (bx, by, bw, bh) in enumerate(valid_boxes, 1):
                    cx, cy = bx + bw // 2, by + bh // 2
                    ideal_pad_w = int((bw / ratio - bw) / 2)
                    ideal_pad_h = int((bh / ratio - bh) / 2)
                    
                    pad_l = min(cx - bw // 2, ideal_pad_w)
                    pad_r = min((w - cx) - bw // 2, ideal_pad_w)
                    pad_t = min(cy - bh // 2, ideal_pad_h)
                    pad_b = min((h - cy) - bh // 2, ideal_pad_h)
                    
                    cropped = img[cy-bh//2-pad_t:cy+bh//2+pad_b, cx-bw//2-pad_l:cx+bw//2+pad_r]
                    if cropped.size == 0: continue
                    if is_rotated: cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    
                    t_bytes = t_mb * 1024 * 1024; low, high, best_q = 1, 100, 85
                    for _ in range(10):
                        mid = (low + high) // 2
                        _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, mid])
                        if len(buf) <= t_bytes: best_q = mid; low = mid + 1
                        else: high = mid - 1
                    
                    _, final_buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, best_q])
                    base_raw, _ = os.path.splitext(file_raw_name)
                    out_name = f"{base_raw}_{part_idx}.jpg" if len(valid_boxes) > 1 else f"{base_raw}.jpg"
                    with open(os.path.join(temp_out_dir, out_name), "wb") as f_out: f_out.write(final_buf)
                    saved += 1
            except:
                pass
            progress_bar.progress(idx / num_uploaded)
        
        if saved > 0:
            with zipfile.ZipFile(zip_path, "w") as z:
                for root_dir, _, files in os.walk(temp_out_dir):
                    for f in files: z.write(os.path.join(root_dir, f), f)
            st.session_state.temp_ready = True
            st.rerun()

    if getattr(st.session_state, "temp_ready", False) and os.path.exists(zip_path):
        st.markdown(L["success"].format(num_uploaded))
        with open(zip_path, "rb") as f_zip: zip_data = f_zip.read()
        if st.download_button(label=L["dl_btn"], data=zip_data, file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True):
            if not user_authed:
                if db and visitor_ip != "127.0.0.1":
                    db.collection("guest_ips").document(visitor_ip).set({
                        "day_used": guest_used_day + num_uploaded, "month_used": guest_used_month + num_uploaded,
                        "last_date": current_date_str, "last_month": current_month_str
                    })
            else:
                if db and user_uid: db.collection("users").document(user_uid).update({"credits_total": max(0, credits_total - num_uploaded)})
            st.session_state.uploader_key_token += 1
            st.session_state.temp_ready = False
            st.rerun()
