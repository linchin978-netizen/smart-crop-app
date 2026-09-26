import os, io, zipfile, cv2, gc, shutil, hashlib, numpy as np
from PIL import Image
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from rembg import remove, new_session
from datetime import datetime

# =========================================================================
# 👑 第一部分：頂層狀態機與初始化防線
# =========================================================================
if "user_authenticated" not in st.session_state: st.session_state.user_authenticated = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "uploader_key_token" not in st.session_state: st.session_state.uploader_key_token = 1000
if "temp_ready" not in st.session_state: st.session_state.temp_ready = False
if "master_preview_dict" not in st.session_state: st.session_state.master_preview_dict = {}

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
            if "X-Forwarded-For" in headers: return headers["X-Forwarded-For"].split(",").strip()
            elif "X-Real-IP" in headers: return headers["X-Real-IP"].strip()
    except: pass
    return "127.0.0.1"

L = {
    "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
    "param_header": "⚙️ Layout Ratio & Capacity Parameters (Customizable Values)",
    "ratio_lbl": "Target subject density ratio (10-99%):",
    "size_lbl": "Maximum payload weight constraint per image (MB):",
    "drag_lbl": "📥 DROP ENTIRE IMAGE FOLDER HERE (Keeps original filenames format)",
    "clear_btn": "🗑 Clear & Reset Queue",
    "btn_lbl": "🚀 One-Click Quick Export Centered Photos",
    "dl_btn": "🎁 Download Centering Assets Package (ZIP)",
    "usage_title": "📊 NEXUS CROP PREMIUM WALLET",
    "preview_title": "🎨 AI Auto-Centering Real-time Matrix Grid (Reject Before Download)",
    "orig_lbl": "📥 Original Asset",
    "del_btn": "🗑 Reject & Remove File"
}

# =========================================================================
# 👑 第二部分：雙軌制 18 點免費滾動死鎖計費大腦
# =========================================================================
st.set_page_config(page_title="NEXUS CROP — AI Unified SaaS", page_icon="🌐", layout="wide")

visitor_ip = get_remote_ip()
current_date_str = datetime.now().strftime("%Y-%m-%d")
current_month_str = datetime.now().strftime("%Y-%m")

guest_used_day, guest_used_month = 0, 0
user_wallet_total = 0   
user_free_day = 0       
user_free_month = 0     
user_authed = st.session_state.user_authenticated
user_uid = ""

# 🛡️ 👑 【開發者實體外網 IP 白名單防線】：已填入您提供的 3 組實體外網 IP！
DEVELOPER_IP_WHITELIST = ["10.12.1.25", "10.12.123.18", "10.12.133.50"]

# 判斷當前連線是否為開發者本人（本機 127.0.0.1 或 命中外網白名單）
is_developer_bypass = (visitor_ip == "127.0.0.1" or visitor_ip in DEVELOPER_IP_WHITELIST)

if db and not is_developer_bypass:
    if not user_authed:
        try:
            ip_data = db.collection("guest_ips").document(visitor_ip).get().to_dict()
            if ip_data:
                if ip_data.get("last_month") == current_month_str: guest_used_month = ip_data.get("month_used", 0)
                if ip_data.get("last_date") == current_date_str: guest_used_day = ip_data.get("day_used", 0)
        except: pass
    else:
        try:
            user_rec = auth.get_user_by_email(st.session_state.user_email)
            user_uid = user_rec.uid
            user_data = db.collection("users").document(user_uid).get().to_dict()
            if user_data:
                user_wallet_total = user_data.get("credits_total", 0)
                if user_data.get("last_month") == current_month_str: user_free_month = user_data.get("monthly_free_used", 0)
                if user_data.get("last_date") == current_date_str: user_free_day = user_data.get("daily_free_used", 0)
        except: user_wallet_total = 50

if is_developer_bypass:
    current_remaining_quota = 999
    display_today_allowance = 6
else:
    if not user_authed:
        if guest_used_month >= 18:
            current_remaining_quota = 0
            display_today_allowance = 6
        else:
            current_remaining_quota = min(max(0, 6 - guest_used_day), max(0, 18 - guest_used_month))
            display_today_allowance = max(0, 6 - guest_used_day)
    else:
        if user_free_month >= 18:
            actual_today_free_allowance = 0
            display_today_allowance = 6
        else:
            actual_today_free_allowance = min(max(0, 6 - user_free_day), max(0, 18 - user_free_month))
            display_today_allowance = max(0, 6 - user_free_day)
        current_remaining_quota = actual_today_free_allowance + user_wallet_total

# 排版佈局
main_col, side_col = st.columns([0.72, 0.28], gap="large")
wallet_info_placeholder = side_col.empty()

if is_developer_bypass and not user_authed:
    wallet_info_placeholder.success("🛡️ **Nexus God-Mode Whitelist Activated**:\n* Unlimited testing enabled.\n* Firebase billing bypassed.")
    side_col.markdown("---")
elif not user_authed:
    show_quota = 0 if guest_used_month >= 18 else current_remaining_quota
    wallet_info_placeholder.info(
        f"🕒 **Anonymous IP Wallet**:\n"
        f"* Available Today: **{show_quota} / 6** Credits\n"
        f"* Monthly Accumulated: **{guest_used_month} / 18** Used\n\n"
        f"💡 *Note: Daily quota resets back to 6 automatically at midnight (12:00 AM) until monthly cap (18) is reached.*"
    )
    side_col.markdown("---")

if not user_authed:
    auth_mode = side_col.radio("Portal Access", ("Sign In", "Sign Up (Free 50 Credits)"), horizontal=True, key="auth_mode_gate")
    email_in = side_col.text_input("📧 Email", key="auth_email")
    pass_in = side_col.text_input("🔒 Password", type="password", key="auth_pass")
    
    if auth_mode == "Sign Up (Free 50 Credits)":
        if side_col.button("🚀 Establish Account", width="stretch", key="reg_btn"):
            try:
                user = auth.create_user(email=email_in, password=pass_in)
                if db: db.collection("users").document(user.uid).set({
                    "email": email_in, "credits_total": 50, "daily_free_used": 0, "monthly_free_used": 0, "last_date": current_date_str, "last_month": current_month_str
                })
                side_col.success("✅ Account established! Switch to Sign In.")
            except Exception as e: side_col.error(f"❌ Failed: {str(e)}")
    else:
        if side_col.button("⚡ Access Account", width="stretch", key="login_btn"):
            try:
                user_record = auth.get_user_by_email(email_in)
                st.session_state.user_authenticated = True
                st.session_state.user_email = email_in
                st.rerun()
            except Exception as e: side_col.error(f"❌ Failed: {str(e)}")
else:
    show_free_today = 0 if (user_free_month >= 18 and not is_developer_bypass) else display_today_allowance
    show_wallet_display = "∞ (Whitelisted)" if is_developer_bypass else user_wallet_total
    
    wallet_info_placeholder.success(
        f"👋 **Welcome, Premium Partner**:\n"
        f"`{st.session_state.user_email}`\n\n"
        f"🎁 **Daily Free Perks**: **{show_free_today} / 6** Credits (Monthly Free: {user_free_month}/18)\n"
        f"🪙 **Lifetime Balance**: **{show_wallet_display}** Credits (Never Expire)"
    )
    side_col.markdown("---")
    side_col.markdown("#### 🪙 Top Up Credits Wallet (Lifetime Access)")
    
    if side_col.button(r"🇺🇸 Starter Pack (\$4.99) ── +150 Credits", width="stretch", key="side_pack_1"):
        if db and user_uid and not is_developer_bypass: 
            db.collection("users").document(user_uid).update({"credits_total": user_wallet_total + 150})
        st.rerun()
        
    if side_col.button(r"🇺🇸 Power Seller (\$19.99) ── +700 Credits", width="stretch", key="side_pack_2"):
        if db and user_uid and not is_developer_bypass: 
            db.collection("users").document(user_uid).update({"credits_total": user_wallet_total + 700})
        st.rerun()
        
    if side_col.button(r"🇺🇸 Mega Vault (\$49.99) ── +2000 Credits", width="stretch", type="primary", key="side_pack_3"):
        if db and user_uid and not is_developer_bypass: 
            db.collection("users").document(user_uid).update({"credits_total": user_wallet_total + 2000})
        st.rerun()
        
    if side_col.button("🚪 Sign Out Workspace", width="stretch", key="logout_btn"):
        st.session_state.user_authenticated = False
        st.session_state.user_email = ""
        st.rerun()
        # =========================================================================
# 👑 第三部分：主工作台佈局面板 (回歸最純淨的大框框)
# =========================================================================
main_col.title(L["title"])
main_col.write("---")
main_col.markdown(f"#### {L['param_header']}")

col_p1, col_p2 = main_col.columns(2)
ratio_str = col_p1.text_input(L["ratio_lbl"], value="90", key="crop_ratio")
try: ratio = max(10.0, min(99.0, float(ratio_str))) / 100.0
except: ratio = 0.90

size_str = col_p2.text_input(L["size_lbl"], value="2.0", key="file_size_max")
try: t_mb = max(0.1, float(size_str))
except: t_mb = 2.0

# 👑 【全局快取刷新防線】：引入動態換鎖 key，只要下方觸發刪除，大框框快取會在一微秒內全自動清洗，徹底打破 React DOM 快取死鎖！
raw_uploaded_files = main_col.file_uploader(L["drag_lbl"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"uploader_core_{st.session_state.uploader_key_token}")

# 🚫 檔名自動去重過濾防線
uploaded_files = []
if raw_uploaded_files:
    seen_names = set()
    for f in raw_uploaded_files:
        if f.name not in seen_names:
            seen_names.add(f.name)
            uploaded_files.append(f)

num_uploaded = len(uploaded_files) if uploaded_files else 0

col_btn1, col_btn2 = main_col.columns(2)
clear_btn_triggered = col_btn1.button(L["clear_btn"], width="stretch", key="clear_all_queue")
if clear_btn_triggered:
    st.session_state.uploader_key_token += 1
    st.session_state.temp_ready = False
    st.session_state.master_preview_dict = {}
    st.rerun()

start_btn = col_btn2.button(L["btn_lbl"], type="primary", width="stretch", key="start_pipeline", disabled=(num_uploaded == 0))

zip_path = "/tmp/processed_centered_images.zip"
if uploaded_files and start_btn:
    saved = 0
    session = load_rembg_session()
    
    # 🧠 增量防禦：如果圖片已經徹底被移出上傳框，才從記憶體中完全拔除
    active_uploaded_names = {f.name for f in uploaded_files}
    for old_key in list(st.session_state.master_preview_dict.keys()):
        if old_key not in active_uploaded_names:
            st.session_state.master_preview_dict.pop(old_key, None)
            
    temp_out_dir = "/tmp/processed_centered_images"
    if os.path.exists(temp_out_dir): shutil.rmtree(temp_out_dir)
    if os.path.exists(zip_path): os.remove(zip_path)
    os.makedirs(temp_out_dir, exist_ok=True)
    
    # 👑 【商用切片大腦】：計算目前新名額
    current_live_sources = sum(1 for k, v in st.session_state.master_preview_dict.items() if isinstance(v, dict) and v["crops"])
    allowed_new_slots = max(0, current_remaining_quota - current_live_sources)
    
    already_processed_files = [f for f in uploaded_files if f.name in st.session_state.master_preview_dict]
    brand_new_files = [f for f in uploaded_files if f.name not in st.session_state.master_preview_dict]
    
    allowed_new_files = brand_new_files[:allowed_new_slots]
    skipped_count = len(brand_new_files) - len(allowed_new_files)
    
    final_execution_queue = already_processed_files + allowed_new_files
    num_execution = len(final_execution_queue)
    
    if skipped_count > 0:
        main_col.warning(f"⚠️ **Nexus Cap Limit Notice**: Available balance only has **{current_remaining_quota}** credits left. {skipped_count} files were skipped. Recharge below to unlock full folder rendering!")

    progress_bar = main_col.progress(0)
    
    for idx, file in enumerate(final_execution_queue, 1):
        file_raw_name = file.name
        
        try:
            # 🛡️ 智慧增量鎖：只要以前跑過且資料存在，直接 0 毫秒跳過不重複計算
            if file_raw_name in st.session_state.master_preview_dict and isinstance(st.session_state.master_preview_dict[file_raw_name], dict):
                saved += len(st.session_state.master_preview_dict[file_raw_name]["crops"])
                progress_bar.progress(idx / num_execution)
                continue
                
            # 💾 強制歸零指標
            file.seek(0)
            file_data_bytes = file.read()
            file.seek(0)
            
            file_bytes = np.frombuffer(file_data_bytes, dtype=np.uint8)
            img_orig = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            del file_bytes, file_data_bytes
            if img_orig is None: continue
            
            _, orig_thumb_buf = cv2.imencode(".jpg", img_orig, [cv2.IMWRITE_JPEG_QUALITY, 35])
            st.session_state.master_preview_dict[file_raw_name] = {"orig_thumb": orig_thumb_buf.tobytes(), "crops": []}
            del orig_thumb_buf
            
            h_o, w_o, _ = img_orig.shape
            max_side = max(h_o, w_o)
            if max_side > 1200:
                scale = 1200.0 / max_side
                img_for_ai = cv2.resize(img_orig, (int(w_o * scale), int(h_o * scale)), interpolation=cv2.INTER_AREA)
            else:
                img_for_ai = img_orig.copy()
            
            # 正向盲測
            img_rgb_o = cv2.cvtColor(img_for_ai, cv2.COLOR_BGR2RGB)
            output_pil_o = remove(Image.fromarray(img_rgb_o), session=session)
            alpha_o = cv2.cvtColor(np.array(output_pil_o), cv2.COLOR_RGBA2BGRA)[:, :, 3]
            _, thresh_o = cv2.threshold(alpha_o, 10, 255, cv2.THRESH_BINARY)
            if max_side > 1200: thresh_o = cv2.resize(thresh_o, (w_o, h_o), interpolation=cv2.INTER_NEAREST)
            contours_normal, _ = cv2.findContours(thresh_o, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            del img_rgb_o, output_pil_o, alpha_o, thresh_o
            
            # 旋轉盲測
            img_rotated = cv2.rotate(img_for_ai, cv2.ROTATE_90_CLOCKWISE)
            img_rgb_r = cv2.cvtColor(img_rotated, cv2.COLOR_BGR2RGB)
            output_pil_r = remove(Image.fromarray(img_rgb_r), session=session)
            alpha_r = cv2.cvtColor(np.array(output_pil_r), cv2.COLOR_RGBA2BGRA)[:, :, 3]
            _, thresh_r = cv2.threshold(alpha_r, 10, 255, cv2.THRESH_BINARY)
            if max_side > 1200: thresh_r = cv2.resize(thresh_r, (h_o, w_o), interpolation=cv2.INTER_NEAREST)
            contours_rotated, _ = cv2.findContours(thresh_r, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            del img_for_ai, img_rotated, img_rgb_r, output_pil_r, alpha_r, thresh_r
            gc.collect()
            
            if sum(1 for c in contours_rotated if cv2.contourArea(cv2.convexHull(c)) > (h_o * w_o * 0.015)) > sum(1 for c in contours_normal if cv2.contourArea(cv2.convexHull(c)) > (w_o * h_o * 0.015)):
                img = cv2.rotate(img_orig, cv2.ROTATE_90_CLOCKWISE); contours = contours_rotated; is_rotated_for_calculation = True; h, w = w_o, h_o
            else:
                img = img_orig; contours = contours_normal; is_rotated_for_calculation = False; h, w = h_o, w_o
            
            valid_boxes = []
            for c in contours:
                hull = cv2.convexHull(c)
                if cv2.contourArea(hull) > (w * h * 0.015):
                    bx, by, bw, bh = cv2.boundingRect(hull); roi = img[by:by+bh, bx:bx+bw]
                    if roi.size > 0:
                        g_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                        e_roi = cv2.Canny(g_roi, 50, 150)
                        if e_roi.size > 0 and (np.sum(e_roi > 0) / e_roi.size) < 0.05:
                            roi_h, roi_w, _ = roi.shape
                            roi_light = cv2.resize(roi, (int(roi_w * (600.0 / max(roi_h, roi_w))), int(roi_h * (600.0 / max(roi_h, roi_w)))), interpolation=cv2.INTER_AREA) if max(roi_h, roi_w) > 600 else roi.copy()
                            s_alpha = cv2.cvtColor(np.array(remove(Image.fromarray(cv2.cvtColor(roi_light, cv2.COLOR_BGR2RGB)), session=session)), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                            # 👑 【完璧去毒修正】：使用正確的標準二值化語法，徹底斬草除根 stroke 錯誤參數！
                            _, s_thresh = cv2.threshold(s_alpha, 10, 255, cv2.THRESH_BINARY)
                            if max(roi_h, roi_w) > 600: s_thresh = cv2.resize(s_thresh, (roi_w, roi_h), interpolation=cv2.INTER_NEAREST)
                            s_cnt, _ = cv2.findContours(s_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                            if s_cnt:
                                sbx, sby, sbw, sbh = cv2.boundingRect(max(s_cnt, key=cv2.contourArea))
                                if sbw * sbh < (bw * bh * 0.92): valid_boxes.append((bx + sbx, by + sby, sbw, sbh)); continue
                    valid_boxes.append((bx, by, bw, bh))
            
            if not valid_boxes: valid_boxes.append((int(w*0.25), int(h*0.25), int(w*0.5), int(w*0.5)))
            
            for part_idx, (bx, by, bw, bh) in enumerate(valid_boxes, 1):
                cx, cy = bx + bw // 2, by + bh // 2
                ideal_pad_w = int((bw / ratio - bw) / 2); ideal_pad_h = int((bh / ratio - bh) / 2)
                x1 = cx - bw // 2 - min(cx - bw // 2, ideal_pad_w); x2 = cx + bw // 2 + min((w - cx) - bw // 2, ideal_pad_w)
                y1 = cy - bh // 2 - min(cy - bh // 2, ideal_pad_h); y2 = cy + bh // 2 + min((h - cy) - bh // 2, ideal_pad_h)
                cropped = img[y1:y2, x1:x2]
                if cropped.size == 0: continue
                if is_rotated_for_counter: cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)
                
                _, cropped_thumb_buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, 35])
                t_bytes = t_mb * 1024 * 1024; low, high, best_q = 1, 100, 85
                for _ in range(10):
                    mid = (low + high) // 2
                    _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, mid])
                    if len(buf) <= t_bytes: best_q = mid; low = mid + 1
                    else: high = mid - 1
                _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, best_q])
                
                base_name, _ = os.path.splitext(file_raw_name)
                out_img_name = f"{base_name}_crop_{part_idx}.jpg" if len(valid_boxes) > 1 else f"{base_name}.jpg"
                st.session_state.master_preview_dict[file_raw_name]["crops"].append({"img_name": out_img_name, "thumb_bytes": cropped_thumb_buf.tobytes(), "full_bytes": buf.tobytes()})
            del img, cropped, contours, valid_boxes
            gc.collect()
        except:
            pass
        progress_bar.progress(idx / num_execution)
    
    # 👑 一鍵導出秒清空黑科技
    st.session_state.uploader_key_token += 1
    st.session_state.temp_ready = True
    st.rerun()
    # =========================================================================
# 👑 第五部分：即時打包 ＋ 180px橫向等高流式矩陣與點對點精準物理拔除
# =========================================================================
if st.session_state.temp_ready and st.session_state.master_preview_dict:
    temp_out_dir = "/tmp/processed_centered_images"
    if os.path.exists(temp_out_dir): shutil.rmtree(temp_out_dir)
    os.makedirs(temp_out_dir, exist_ok=True)
    if os.path.exists(zip_path): os.remove(zip_path)
    
    total_live_count = 0
    distinct_source_files_count = 0
    
    for orig_file, contents in list(st.session_state.master_preview_dict.items()):
        if isinstance(contents, dict) and contents.get("crops"):
            distinct_source_files_count += 1 
            for crop_item in contents["crops"]:
                with open(os.path.join(temp_out_dir, crop_item["img_name"]), "wb") as f_out: 
                    f_out.write(crop_item["full_bytes"])
                total_live_count += 1
            
    if total_live_count > 0:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(temp_out_dir):
                for f in files: zip_file.write(os.path.join(root, f), f)
                
        with open(zip_path, "rb") as f_zip: zip_data = f_zip.read()
        
        dl_clicked = main_col.download_button(label=L["dl_btn"], data=zip_data, file_name="processed_centered_images.zip", mime="application/zip", width="stretch", key="dl_zip_final_gate")
        
        if dl_clicked:
            final_deduct_credits = distinct_source_files_count
            is_developer_bypass = (visitor_ip == "127.0.0.1" or visitor_ip in DEVELOPER_IP_WHITELIST)
            
            if db and not is_developer_bypass:
                if not user_authed:
                    db.collection("guest_ips").document(visitor_ip).set({"day_used": guest_used_day + final_deduct_credits, "month_used": guest_used_month + final_deduct_credits, "last_date": current_date_str, "last_month": current_month_str})
                elif user_uid:
                    member_monthly_free_left = max(0, 18 - user_free_month) 
                    member_daily_free_left = max(0, 6 - user_free_day)     
                    actual_today_free_left = min(member_daily_free_left, member_monthly_free_left)
                    if final_deduct_credits <= actual_today_free_left:
                        new_daily_free_used = user_free_day + final_deduct_credits
                        new_monthly_free_used = user_free_month + final_deduct_credits
                        new_wallet_total = user_wallet_total
                    else:
                        overflow_debt = final_deduct_credits - actual_today_free_left
                        new_daily_free_used = user_free_day + actual_today_free_left
                        new_monthly_free_used = user_free_month + actual_today_free_left
                        new_wallet_total = max(0, user_wallet_total - overflow_debt)
                    db.collection("users").document(user_uid).update({"credits_total": new_wallet_total, "daily_free_used": new_daily_free_used, "monthly_free_used": new_monthly_free_used, "last_date": current_date_str, "last_month": current_month_str})
            
            st.session_state.temp_ready = False
            st.session_state.master_preview_dict = {}
            st.rerun()

    st.html("""
        <style>
            div[data-testid="stImage"] img { height: 180px !important; object-fit: contain !important; width: auto !important; max-width: 100% !important; margin: 0 auto; }
            div[data-testid="stColumn"] { display: flex; flex-direction: column; justify-content: space-between; }
        </style>
    """)

    main_col.write("---")
    main_col.markdown(f"### {L['preview_title']}")
    
    for orig_key, contents in list(st.session_state.master_preview_dict.items()):
        if not isinstance(contents, dict) or not contents.get("crops"): continue
        
        main_col.markdown(f"#### 📁 Asset Source Name: `{orig_key}`")
        num_crops = len(contents["crops"])
        layout_cols = main_col.columns([0.20, 0.80], gap="medium")
        
        # 👑 【完璧修正防線】：精準指定 layout_cols[0] 渲染左側原圖，徹底消滅 Context Manager Bug！
        with layout_cols[0]: 
            st.image(contents["orig_thumb"], caption=L["orig_lbl"], width="stretch")
            
        # 👑 【完璧修正防線】：精準指定 layout_cols[1] 渲染右側橫向流式裁切子圖
        with layout_cols[1]:
            sub_grid_cols = st.columns(num_crops)
            for c_idx, crop_data in enumerate(contents["crops"]):
                with sub_grid_cols[c_idx]:
                    st.image(crop_data["thumb_bytes"], width="stretch")
                    st.caption(f"🎯 {crop_data['img_name']}")
                    btn_id = f"del_{orig_key}_{crop_data['img_name']}_{c_idx}"
                    
                    if st.button(L["del_btn"], key=btn_id, type="secondary", width="stretch"):
                        st.session_state.master_preview_dict[orig_key]["crops"] = [x for x in st.session_state.master_preview_dict[orig_key]["crops"] if x['img_name'] != crop_data['img_name']]
                        
                        # 👑 【純淨物理剔除】：下方不管刪一半、全刪光，直接 pop 剔除
                        #    因為上面大框框在點擊導出的那一秒早就已經被強制自動全清空了，
                        #    所以使用者如果要反悔，直接再拉一次檔案點導出，100% 原地大復活！
                        if not st.session_state.master_preview_dict[orig_key]["crops"]:
                            st.session_state.master_preview_dict.pop(orig_key, None)
                        st.rerun()
