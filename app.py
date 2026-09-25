import os, io, zipfile, cv2, gc, shutil, hashlib, numpy as np
from PIL import Image
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from rembg import remove, new_session
from datetime import datetime

# 👑 最高安全狀態機前置初始化：建立全自動預覽快取帳本與持久化快取
if "user_authenticated" not in st.session_state: st.session_state.user_authenticated = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "uploader_key_token" not in st.session_state: st.session_state.uploader_key_token = 1000
if "temp_ready" not in st.session_state: st.session_state.temp_ready = False
if "master_preview_dict" not in st.session_state: st.session_state.master_preview_dict = {}

# 👑 Firebase 雲端保險箱最高安全初始化連線晶片
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
            if "X-Forwarded-For" in headers: return headers["X-Forwarded-For"].split(",")[0].strip()
            elif "X-Real-IP" in headers: return headers["X-Real-IP"].strip()
    except: pass
    return "127.0.0.1"

# 🌍 航太級輕量化本地語系字典（徹底根除龐大字典造成的傳輸溢出死穴！）
L = {
    "title": "🌐 網拍電商商品照片 智慧置中裁剪系統 SaaS",
    "param_header": "⚙️ 圖檔比例容量參數設定 (可自訂數值)",
    "ratio_lbl": "導出後主體佔畫面比例 (10-99%):",
    "size_lbl": "導出後照片檔最大容量限制 (MB):",
    "drag_lbl": "📥 將圖片或整個圖片資料夾拖曳至此（原檔名導出流，免註冊免費體驗）",
    "clear_btn": "🗑 清除重選",
    "btn_lbl": "🚀 一鍵快速導出完美置中商品照片",
    "dl_btn": "🎁 點擊下載完美置中相片壓縮包 (ZIP)"
}
st.set_page_config(page_title="NEXUS CROP — AI Unified SaaS", page_icon="🌐", layout="wide")

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
            if ip_data.get("last_date") == current_date_str: guest_used_day = ip_data.get("day_used", 0)
            if ip_data.get("last_month") == current_month_str: guest_used_month = ip_data.get("month_used", 0)
    except: pass

if not user_authed:
    current_remaining_quota = min(10 - guest_used_day, 30 - guest_used_month)
else:
    if db:
        try:
            user_rec = auth.get_user_by_email(st.session_state.user_email)
            user_uid = user_rec.uid
            user_data = db.collection("users").document(user_uid).get().to_dict()
            credits_total = user_data.get("credits_total", 0)
        except: credits_total = 50
    current_remaining_quota = credits_total

# 高級電商雙欄布局
main_col, side_col = st.columns([0.72, 0.28], gap="large")

with side_col:
    st.markdown("### 📊 NEXUS CROP 會員錢包看板")
    if not user_authed:
        st.info(f"🕒 免註冊 IP 試用錢包：\n* 今日已用額度：**{guest_used_day} / 10** Credits\n* 💡 剩餘可用總張數：**{max(0, current_remaining_quota)} 張**")
        st.markdown("---")
        auth_mode = st.radio("Portal Access", ("Sign In", "Sign Up (Free 50)"), horizontal=True)
        email_in = st.text_input("📧 Email", key="auth_email")
        pass_in = st.text_input("🔒 Password", type="password", key="auth_pass")
        if auth_mode == "Sign Up (Free 50)":
            if st.button("🚀 Establish Account", use_container_width=True):
                try:
                    user = auth.create_user(email=email_in, password=pass_in)
                    if db: db.collection("users").document(user.uid).set({"email": email_in, "credits_total": 50, "tier": "PREMIUM_WORKSPACE"})
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
        st.success(f"👋 歡迎回來，尊貴的電商夥伴：\n**{st.session_state.user_email}**\n* 🪙 專屬錢包總餘額：**{credits_total} Credits**")
        st.markdown("---")
        st.markdown("#### 🪙 Top Up Cloud Unified Wallet")
        if st.button(r"🇺🇸 Starter Pack ($4.99) ── +150 Credits", use_container_width=True, key="side_pack_1"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits_total": credits_total + 150})
            st.rerun()
        if st.button(r"🇺🇸 Power Seller ($19.99) ── +700 Credits", use_container_width=True, key="side_pack_2"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits_total": credits_total + 700})
            st.rerun()
        if st.button(r"🇺🇸 Mega Vault ($49.99) ── +2000 Credits", use_container_width=True, type="primary", key="side_pack_3"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits_total": credits_total + 2000})
            st.rerun()
        if st.button("🚪 Sign Out Workspace", use_container_width=True):
            st.session_state.user_authenticated = False
            st.session_state.user_email = ""
            st.rerun()

# 👑 👑 👑 【100% 絕對扁平化、0縮排錯誤防護閘門】 👑 👑 👑
with main_col:
    st.title(L["title"])
    st.write("---")
    st.markdown(f"#### {L['param_header']}")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        ratio_str = st.text_input(L["ratio_lbl"], value="90", key="crop_ratio")
        try: ratio = max(10.0, min(99.0, float(ratio_str))) / 100.0
        except: ratio = 0.90
    with col_p2:
        size_str = st.text_input(L["size_lbl"], value="2.0", key="file_size_max")
        try: t_mb = max(0.1, float(size_str))
        except: t_mb = 2.0

    uploaded_files = st.file_uploader(L["drag_lbl"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"uploader_core_{st.session_state.uploader_key_token}")
    num_uploaded = len(uploaded_files) if uploaded_files else 0

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(L["clear_btn"], use_container_width=True, key="clear_all_queue"):
            st.session_state.uploader_key_token += 1
            st.session_state.temp_ready = False
            st.session_state.master_preview_dict = {}
            st.rerun()
    with col_btn2:
        any_violation = (num_uploaded == 0 or num_uploaded > current_remaining_quota)
        start_btn = st.button(L["btn_lbl"], type="primary", use_container_width=True, key="start_pipeline", disabled=any_violation)

    zip_path = "/tmp/processed_centered_images.zip"
    if uploaded_files and start_btn:
        saved = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        session = load_rembg_session()
        
        st.session_state.master_preview_dict = {} # 🎯 開刀前完美洗淨預覽快取帳本
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
                
                # 👑 為了平行顯示，在此秒級就地生成 50KB 原圖縮圖快取
                _, orig_thumb_buf = cv2.imencode(".jpg", img_orig, [cv2.IMWRITE_JPEG_QUALITY, 35])
                st.session_state.master_preview_dict[file_raw_name] = {
                    "orig_thumb": orig_thumb_buf.tobytes(),
                    "crops": []
                }
                # 👑 A 版完全體原裝精準演算法：直版盲測解算
                img_rgb_o = cv2.cvtColor(img_orig, cv2.COLOR_BGR2RGB)
                output_pil_o = remove(Image.fromarray(img_rgb_o), session=session)
                alpha_o = cv2.cvtColor(np.array(output_pil_o), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                _, thresh_o = cv2.threshold(alpha_o, 10, 255, cv2.THRESH_BINARY)
                contours_normal, _ = cv2.findContours(thresh_o, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # 👑 A 版完全體原裝精準演算法：橫版轉90度盲測解算
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
                
                if valid_cnt_rotated > valid_cnt_normal:
                    img = img_rotated; contours = contours_rotated; is_rotated_for_calculation = True; h, w = h_r, w_r
                else:
                    img = img_orig; contours = contours_normal; is_rotated_for_calculation = False; h, w = h_o, w_o
                
                valid_boxes = []
                # 👑 👑 👑 完美還原您桌面 A 版最核心的「92% 大框替換子邊界熔斷過濾晶片」
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
                    # 👑 👑 👑 完美還原您桌面 A 版最核心的「最大化純原圖自適應物理邊界卡位算法」
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
                    
                    # 👑 雙軌流：秒級就地壓出一張 50KB 1/3 極輕量預覽縮圖
                    _, cropped_thumb_buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, 35])
                    
                    t_bytes = t_mb * 1024 * 1024; low, high, best_q = 1, 100, 85
                    for _ in range(10):
                        mid = (low + high) // 2
                        _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, mid])
                        if len(buf) <= t_bytes: best_q = mid; low = mid + 1
                        else: high = mid - 1
                    _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, best_q])
                    
                    base_name, _ = os.path.splitext(file_raw_name)
                    out_img_name = f"{base_name}_裁切_{part_idx}.jpg" if len(valid_boxes) > 1 else f"{base_name}.jpg"
                    
                    # 🎯 裝填進全新的預覽大字典，包含完整實體二進位包，留給外層進行無耗費剔除！
                    st.session_state.master_preview_dict[file_raw_name]["crops"].append({
                        "img_name": out_img_name,
                        "thumb_bytes": cropped_thumb_buf.tobytes(),
                        "full_bytes": buf.tobytes()
                    })
                    saved += 1
            except: pass
            progress_bar.progress(idx / num_uploaded)
        
        if saved > 0:
            st.session_state.temp_ready = True
            st.rerun()
            # 🔓 🔓 🔓 【持久化安全放行閘門 ── 擺脫 Rerun 時空死鎖，在最外層強勢渲染！】 🔓 🔓 🔓
    if st.session_state.temp_ready and st.session_state.master_preview_dict:
        
        # 👑 動態物理打包晶片：每一次渲染，只打包「目前還留在字典裡、沒被賣家砍掉」的生還照片！
        temp_out_dir = "/tmp/processed_centered_images"
        if os.path.exists(temp_out_dir): shutil.rmtree(temp_out_dir)
        os.makedirs(temp_out_dir, exist_ok=True)
        if os.path.exists(zip_path): os.remove(zip_path)
        
        total_live_count = 0
        for orig_file, contents in list(st.session_state.master_preview_dict.items()):
            for crop_item in contents["crops"]:
                with open(os.path.join(temp_out_dir, crop_item["img_name"]), "wb") as f_out:
                    f_out.write(crop_item["full_bytes"])
                total_live_count += 1
                
        if total_live_count > 0:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, _, files in os.walk(temp_out_dir):
                    for f in files: zip_file.write(os.path.join(root, f), f)
                    
            with open(zip_path, "rb") as f_zip: zip_data = f_zip.read()
            
            # 🔓 下載按鈕正式亮起
            if st.download_button(label=L["dl_btn"], data=zip_data, file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True, key="dl_zip_final_gate"):
                if db and visitor_ip != "127.0.0.1" and not user_authed:
                    db.collection("guest_ips").document(visitor_ip).set({
                        "day_used": guest_used_day + num_uploaded, "month_used": guest_used_month + num_uploaded,
                        "last_date": current_date_str, "last_month": current_month_str
                    })
                elif db and user_uid and user_authed:
                    db.collection("users").document(user_uid).update({"credits_total": max(0, credits_total - num_uploaded)})
                    
                st.session_state.uploader_key_token += 1
                st.session_state.temp_ready = False
                st.session_state.master_preview_dict = {}
                st.rerun()
                # 🎨 🎨 🎨 【全新重頭戲：左原圖 ── 右 1/3 對照微型網格看板 ＋ 物理剔除剔除按鈕晶片】 🎨 🎨 🎨
        st.write("---")
        st.markdown("### 🎨 AI 完美置中成果實時對照網格 (下載前不滿意免費剔除區)")
        
        for orig_key, contents in list(st.session_state.master_preview_dict.items()):
            if not contents["crops"]: continue # 如果這張照片底下的裁切都被砍光了，就地放行
            
            st.markdown(f"#### 📁 圖片來源母檔：`{orig_key}`")
            
            # 👑 黃金三橫列分配：左邊原圖 25% 大幅卡位，右邊 1/3 智慧精細並排長出 crops
            layout_cols = st.columns([0.25, 0.75])
            with layout_cols[0]:
                st.image(contents["orig_thumb"], caption="📥 原始上傳母圖", use_container_width=True)
                
            with layout_cols[1]:
                # 在右側大框架裡，以 3 縱列微型網格精美向下排列（剛好滿足 1/3 大小大略肉眼檢查需求）
                sub_grid_cols = st.columns(3)
                for c_idx, crop_data in enumerate(contents["crops"]):
                    with sub_grid_cols[c_idx % 3]:
                        st.image(crop_data["thumb_bytes"], use_container_width=True)
                        st.caption(f"🎯 {crop_data['img_name']}")
                        
                        # 🗑 紅色物理剔除晶片：點擊一瞬間，只在記憶體中蒸發，完全不扣點、不進 ZIP 包！
                        btn_id = f"del_{orig_key}_{crop_data['img_name']}_{c_idx}"
                        if st.button("🗑 刪除此張不下載", key=btn_id, type="secondary", use_container_width=True):
                            st.session_state.master_preview_dict[orig_key]["crops"].pop(c_idx)
                            # 如果整張母圖裡裁出來的子主體都被砍光了，將母圖帳本集體抹除
                            if not st.session_state.master_preview_dict[orig_key]["crops"]:
                                st.session_state.master_preview_dict.pop(orig_key)
                            st.rerun()
