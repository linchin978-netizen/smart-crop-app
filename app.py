import os, io, zipfile, cv2, gc, shutil, hashlib, numpy as np
from PIL import Image
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from rembg import remove, new_session
from datetime import datetime

# 👑 頂層狀態機初始化最前置防線：一開機立刻強制寫入記憶體，100% 防止順序 KeyError 車禍
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
    except: pass

db = firestore.client() if firebase_admin._apps else None

@st.cache_resource
def load_rembg_session(): return new_session("silueta")

def get_remote_ip():
    try:
        ctx = st.context if hasattr(st, "context") else None
        if ctx and hasattr(ctx, "headers"):
            if "X-Forwarded-For" in ctx.headers: return ctx.headers["X-Forwarded-For"].split(",").strip()
            elif "X-Real-IP" in ctx.headers: return ctx.headers["X-Real-IP"].strip()
    except: pass
    return "127.0.0.1"

# 🌍 核心功能純英文大字典 (SaaS 旗艦規格)
L = {
    "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
    "param_header": "⚙️ Layout Ratio & Capacity Parameters",
    "ratio_lbl": "Target subject density ratio (10-99%):",
    "size_lbl": "Maximum weight constraint per image (MB):",
    "drag_lbl": "📥 DROP IMAGE FOLDER HERE",
    "clear_btn": "🗑 Clear Reset Queue",
    "btn_lbl": "🚀 One-Click Export Centered Photos",
    "dl_btn": "🎁 Download Assets Package (ZIP)",
    "usage_title": "📊 PREMIUM WORKSPACE WALLET",
    "guest_info": "🕒 Anonymous IP Wallet:\n* Today Used: **{} / 10** Credits\n* 💡 Available Balance: **{} items**",
    "welcome": "👋 Welcome, Premium Partner:\n**{}**\n* 🪙 Active Wallet: **{} Credits**",
    "success": "### ✅ Render Completed!",
    "preview_title": "🎨 AI Auto-Centering Real-time Matrix Grid (Reject Before Download)",
    "orig_lbl": "📥 Original Asset",
    "del_btn": "🗑 Reject & Remove"
}
st.set_page_config(page_title="NEXUS CROP — AI Unified SaaS", page_icon="🌐", layout="wide")

visitor_ip = get_remote_ip()
current_date_str = datetime.now().strftime("%Y-%m-%d")
current_month_str = datetime.now().strftime("%Y-%m")

guest_used_day, guest_used_month = 0, 0
user_authed = st.session_state.user_authenticated
credits_total = 0
user_uid = ""

if db and not user_authed and visitor_ip != "127.0.0.1":
    try:
        ip_data = db.collection("guest_ips").document(visitor_ip).get().to_dict()
        if ip_data:
            if ip_data.get("last_date") == current_date_str: guest_used_day = ip_data.get("day_used", 0)
            if ip_data.get("last_month") == current_month_str: guest_used_month = ip_data.get("month_used", 0)
    except: pass

current_remaining_quota = min(10 - guest_used_day, 30 - guest_used_month) if not user_authed else credits_total

# 高級電商雙欄布局
main_col, side_col = st.columns([0.72, 0.28], gap="large")

side_col.markdown(f"### {L['usage_title']}")
if not user_authed:
    side_col.info(L["guest_info"].format(guest_used_day, max(0, current_remaining_quota)))
    side_col.markdown("---")
    auth_mode = side_col.radio("Portal Access", ("Sign In", "Sign Up (Free 50)"), horizontal=True, key="auth_mode_gate")
    email_in = side_col.text_input("📧 Email", key="auth_email")
    pass_in = side_col.text_input("🔒 Password", type="password", key="auth_pass")
    if auth_mode == "Sign Up (Free 50)":
        if side_col.button("🚀 Establish Account", width="stretch", key="reg_btn"):
            try:
                user = auth.create_user(email=email_in, password=pass_in)
                if db: db.collection("users").document(user.uid).set({"email": email_in, "credits_total": 50})
                side_col.success("Account established! Switch to Sign In.")
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
    if db:
        try:
            user_rec = auth.get_user_by_email(st.session_state.user_email)
            user_uid = user_rec.uid
            user_data = db.collection("users").document(user_uid).get().to_dict()
            credits_total = user_data.get("credits_total", 0)
        except: credits_total = 50
    current_remaining_quota = credits_total
    side_col.success(L["welcome"].format(st.session_state.user_email, credits_total))
    side_col.markdown("---")
    side_col.markdown("#### 🪙 Top Up Cloud Unified Wallet")
    if side_col.button(r"🇺🇸 Starter Pack ($4.99) ── +150 Credits", width="stretch", key="side_pack_1"):
        if db and user_uid: db.collection("users").document(user_uid).update({"credits_total": credits_total + 150})
        st.rerun()
    if side_col.button(r"🇺🇸 Power Seller ($19.99) ── +700 Credits", width="stretch", key="side_pack_2"):
        if db and user_uid: db.collection("users").document(user_uid).update({"credits_total": credits_total + 700})
        st.rerun()
    if side_col.button(r"🇺🇸 Mega Vault ($49.99) ── +2000 Credits", width="stretch", type="primary", key="side_pack_3"):
        if db and user_uid: db.collection("users").document(user_uid).update({"credits_total": credits_total + 2000})
        st.rerun()
    if side_col.button("🚪 Sign Out Workspace", width="stretch", key="logout_btn"):
        st.session_state.user_authenticated = False
        st.session_state.user_email = ""
        st.rerun()

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

uploaded_files = main_col.file_uploader(L["drag_lbl"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"uploader_core_{st.session_state.uploader_key_token}")
num_uploaded = len(uploaded_files) if uploaded_files else 0

col_btn1, col_btn2 = main_col.columns(2)
clear_btn_triggered = col_btn1.button(L["clear_btn"], width="stretch", key="clear_all_queue")
if clear_btn_triggered:
    st.session_state.uploader_key_token += 1
    st.session_state.temp_ready = False
    st.session_state.master_preview_dict = {}
    st.rerun()

any_violation = (num_uploaded == 0 or num_uploaded > current_remaining_quota)
start_btn = col_btn2.button(L["btn_lbl"], type="primary", width="stretch", key="start_pipeline", disabled=any_violation)

zip_path = "/tmp/processed_centered_images.zip"

if st.session_state.temp_ready:
    pass
elif not start_btn:
    st.stop()
    # 🔒 🔒 🔒 安全隔離區：else 結構已被物理摧毀，100% 靠最左邊（0 縮排死角） 🔒 🔒 🔒
saved = 0
progress_bar = main_col.progress(0)
session = load_rembg_session()
st.session_state.master_preview_dict = {}
temp_out_dir = "/tmp/processed_centered_images"
if os.path.exists(temp_out_dir): shutil.rmtree(temp_out_dir)
if os.path.exists(zip_path): os.remove(zip_path)
os.makedirs(temp_out_dir, exist_ok=True)

for idx, file in enumerate(uploaded_files, 1):
    try:
        file_raw_name = file.name
        file.seek(0)
        file_bytes = np.frombuffer(file.read(), dtype=np.uint8)
        img_orig = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img_orig is None: continue
        
        _, orig_thumb_buf = cv2.imencode(".jpg", img_orig, [cv2.IMWRITE_JPEG_QUALITY, 35])
        st.session_state.master_preview_dict[file_raw_name] = {
            "orig_thumb": orig_thumb_buf.tobytes(), "crops": []
        }
        
        img_rgb_o = cv2.cvtColor(img_orig, cv2.COLOR_BGR2RGB)
        output_pil_o = remove(Image.fromarray(img_rgb_o), session=session)
        alpha_o = cv2.cvtColor(np.array(output_pil_o), cv2.COLOR_RGBA2BGRA)[:, :, 3]
        _, thresh_o = cv2.threshold(alpha_o, 10, 255, cv2.THRESH_BINARY)
        contours_normal, _ = cv2.findContours(thresh_o, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        img_rotated = cv2.rotate(img_orig, cv2.ROTATE_90_CLOCKWISE)
        img_rgb_r = cv2.cvtColor(img_rotated, cv2.COLOR_BGR2RGB)
        output_pil_r = remove(Image.fromarray(img_rgb_r), session=session)
        alpha_r = cv2.cvtColor(np.array(output_pil_r), cv2.COLOR_RGBA2BGRA)[:, :, 3]
        _, thresh_r = cv2.threshold(alpha_r, 10, 255, cv2.THRESH_BINARY)
        contours_rotated, _ = cv2.findContours(thresh_r, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        h_o, w_o, _ = img_orig.shape
        valid_cnt_normal = sum(1 for c in contours_normal if cv2.contourArea(cv2.convexHull(c)) > (w_o * h_o * 0.015))
        h_r, w_r, _ = img_rotated.shape
        valid_cnt_rotated = sum(1 for c in contours_rotated if cv2.contourArea(cv2.convexHull(c)) > (w_r * h_r * 0.015))
        
        # 👑 🎯 物理抹除 else 車禍：改用預設單向覆蓋，前方 0 縮排，技術上徹底封死 IndentationError！
        img = img_orig; contours = contours_normal; is_rotated_for_calculation = False; h, w = h_o, w_o
        if valid_cnt_rotated > valid_cnt_normal:
            img = img_rotated; contours = contours_rotated; is_rotated_for_calculation = True; h, w = h_r, w_r
            
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
                            sbx, sby, sbw, sbh = cv2.boundingRect(max(s_cnt, key=cv2.contourArea))
                            if sbw * sbh < (bw * bh * 0.92):
                                valid_boxes.append((bx + sbx, by + sby, sbw, sbh))
                                continue
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
            
            x1 = cx - bw // 2 - pad_l; x2 = cx + bw // 2 + pad_r
            y1 = cy - bh // 2 - pad_t; y2 = cy + bh // 2 + pad_b
            
            cropped = img[y1:y2, x1:x2]
            if cropped.size == 0: continue
            if is_rotated_for_calculation: cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            _, cropped_thumb_buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, 35])
            
            t_bytes = t_mb * 1024 * 1024; low, high, best_q = 1, 100, 85
            for _ in range(10):
                mid = (low + high) // 2
                _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, mid])
                if len(buf) <= t_bytes: best_q = mid; low = mid + 1
                else: high = mid - 1
            _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, best_q])
            
            base_name, _ = os.path.splitext(file_raw_name)
            out_img_name = f"{base_name}_crop_{part_idx}.jpg" if len(valid_boxes) > part_idx else f"{base_name}.jpg"
            
            st.session_state.master_preview_dict[file_raw_name]["crops"].append({
                "img_name": out_img_name, "thumb_bytes": cropped_thumb_buf.tobytes(), "full_bytes": buf.tobytes()
            })
            saved += 1
        del img, img_orig, img_rotated, contours_normal, contours_rotated; gc.collect()
    except: pass
    progress_bar.progress(idx / num_uploaded)

if saved > 0:
    st.session_state.temp_ready = True
    st.rerun()

if st.session_state.temp_ready and st.session_state.master_preview_dict:
    temp_out_dir = "/tmp/processed_centered_images"
    if os.path.exists(temp_out_dir): shutil.rmtree(temp_out_dir)
    os.makedirs(temp_out_dir, exist_ok=True)
    if os.path.exists(zip_path): os.remove(zip_path)
    
    total_live_count = 0
    for orig_file, contents in list(st.session_state.master_preview_dict.items()):
        for crop_item in contents["crops"]:
            with open(os.path.join(temp_out_dir, crop_item["img_name"]), "wb") as f_out: f_out.write(crop_item["full_bytes"])
            total_live_count += 1
            
    if total_live_count > 0:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(temp_out_dir):
                for f in files: zip_file.write(os.path.join(root, f), f)
                
        with open(zip_path, "rb") as f_zip: zip_data = f_zip.read()
        
        dl_clicked = main_col.download_button(label=L["dl_btn"], data=zip_data, file_name="processed_centered_images.zip", mime="application/zip", width="stretch", key="dl_zip_final_gate")
        if dl_clicked:
            if db and visitor_ip != "127.0.0.1" and not user_authed:
                db.collection("guest_ips").document(visitor_ip).set({"day_used": guest_used_day + num_uploaded, "month_used": guest_used_month + num_uploaded, "last_date": current_date_str, "last_month": current_month_str})
            elif db and user_uid and user_authed:
                db.collection("users").document(user_uid).update({"credits_total": max(0, credits_total - num_uploaded)})
            st.session_state.uploader_key_token += 1
            st.session_state.temp_ready = False
            st.session_state.master_preview_dict = {}
            st.rerun()

    main_col.write("---")
    main_col.markdown(f"### {L['preview_title']}")
    
    for orig_key, contents in list(st.session_state.master_preview_dict.items()):
        if not contents["crops"]: continue
        
        main_col.markdown(f"#### 📁 Asset Source Name: `{orig_key}`")
        layout_cols = main_col.columns([0.25, 0.75])
        layout_cols.image(contents["orig_thumb"], caption=L["orig_lbl"], width="stretch")
        
        sub_grid_cols = layout_cols.columns(8)
        for c_idx, crop_data in enumerate(contents["crops"]):
            with sub_grid_cols[c_idx % 8]:
                st.image(crop_data["thumb_bytes"], width="stretch")
                st.caption(f"🎯 {crop_data['img_name']}")
                btn_id = f"del_{orig_key}_{crop_data['img_name']}_{c_idx}"
                if st.button(L["del_btn"], key=btn_id, type="secondary", width="stretch"):
                    st.session_state.master_preview_dict[orig_key]["crops"].pop(c_idx)
                    if not st.session_state.master_preview_dict[orig_key]["crops"]: st.session_state.master_preview_dict.pop(orig_key)
                    st.rerun()
