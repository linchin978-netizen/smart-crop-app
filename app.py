import os, io, zipfile, cv2, gc, shutil, hashlib, numpy as np
from PIL import Image
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from rembg import remove, new_session

# 👑 Firebase 雲端保險箱最高安全初始化連線晶片 (從隱形 Secrets 保險箱讀取暗號)
if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        pass

db = firestore.client() if firebase_admin._apps else None

# 👑 雲端快取優化：確保 AI 模型在雲端唯一下載一次，節省效能開銷
@st.cache_resource
def load_rembg_session():
    return new_session("silueta")

def get_ai_bounding_boxes(cv_img, session):
    img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    output_pil = remove(Image.fromarray(img_rgb), session=session)
    alpha = cv2.cvtColor(np.array(output_pil), cv2.COLOR_RGBA2BGRA)[:, :, 3]
    _, thresh = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

# 🌍 跨國網拍 SaaS 8 國語言大字典 (A面：繁體中文、简体中文)
LANG_MAP = {
    "繁體中文": {
        "title": "🌐 網拍電商商品照片 ── 智慧自動置中裁剪系統",
        "subtitle": "卡牌、網拍商品照一鍵自動裁切、主體完美置中、圖檔比例容量自由設定",
        "pricing_html": """
        ### 💰 選擇您的智慧生產力方案 (隨買隨用 Credits 點數包)
        * **🌟 免費體驗**: **$0** (註冊即送 **20 免費點數**！) ── *體驗強大原圖裁切防線。*
        * **🪙 賣家入門包**: **$4.99** (內含 **150 點數** ── *每張完美照片不用 1.1 元台幣！*)
        * **⚡ 大賣家衝刺包**: **$19.99** (內含 **700 點數** ── *每張完美照片不到 0.9 元台幣！*)
        * **👑 跨境卡牌大亨包**: **$49.99** (內含 **2,000 點數** ── **極致極限：每張照片不到 0.8 元台幣！**)
        """,
        "param_header": "⚙️ 圖檔比例容量參數 (可自訂數值)",
        "ratio_lbl": "導出後主體佔畫面比例 (10-99%):",
        "size_lbl": "導出後照片檔最大容量限制 (MB):",
        "drag_lbl": "📥 將「單張相片」或「整個圖片資料夾」全數拖曳至此（智慧解碼原資料夾名稱，免註冊免費體驗）",
        "loaded_lbl": "📊 目前已載入商品照片：{} 張",
        "clear_btn": "🗑 清除重選",
        "btn_lbl": "🚀 一鍵快速導出完美置中商品照片",
        "processing": "⏳ 智慧光學解算中：第 {} 張 / 共 {} 張...",
        "success": "### ✅ 核心解算成功！點數已安全扣除，共生成 {} 張智慧命名置中照片！",
        "dl_btn": "🎁 點擊下載完美置中相片壓縮包 (ZIP)",
        "limit_err": "🔒 抱歉，您的免註冊試用額度已用完。歡迎在右側註冊登入領取會員免費 20 點，或立即充值點數套餐包解鎖更高生產力！",
        "dup_err": "⚠️ 偵測到重複上傳相同照片！框框內不可重複置入相同圖檔（即使更換檔名亦會被安全攔截），請使用清除重選並重新拉入純淨不重複的照片，以防止點數重複扣除爭議！",
        "usage_title": "📊 NEXUS CROP 會員錢包看板",
        "guest_info": "🕒 免註冊試用錢包：\n* 當日已用點數：**{} / 10** Credits\n* 💡 剩餘可用總張數：**{} 張**",
        "welcome": "👋 歡迎回來，尊貴的電商夥伴：**{}** \n* 🪙 免費錢包餘額：**{} Credits** (優先扣除)\n* 🪙 付費錢包餘額：**{} Credits**\n* 💡 剩餘可導出總張數：**{} 張**"
    },
    "简体中文": {
        "title": "🌐 网拍电商商品照片 ── 智慧自动置中裁剪系统",
        "subtitle": "卡牌、网拍商品照一键自动裁切、主体完美置中、图档比例容量自由设定",
        "pricing_html": """
        ### 💰 选择您的智慧生产力方案 (随买随用 Credits 点数包)
        * **🌟 免费体验**: **$0** (注册即送 **20 免费点数**！) ── *体验强大原图裁切防线。*
        * **🪙 卖家入门包**: **$4.99** (内含 **150 点数** ── *每张完美照片不到 0.23 元人民币！*)
        * **⚡ 大卖家冲刺包**: **$19.99** (内含 **700 点数** ── *每张完美照片不到 0.20 元人民币！*)
        * **👑 跨境卡牌大亨包**: **$49.99** (内含 **2,000 点数** ── **极致极限：每张照片不到 0.17 元人民币！**)
        """,
        "param_header": "⚙️ 图档比例容量参数 (可自订数值)",
        "ratio_lbl": "导出后主体占画面比例 (10-99%):",
        "size_lbl": "导出后照片档 maximum 容量限制 (MB):",
        "drag_lbl": "📥 将单张相片 or 整个图片文件夹全数拖拽至此（智慧解码原文件夹名称，免注册免费体验）",
        "loaded_lbl": "📊 目前已载入商品照片：{} 张",
        "clear_btn": "🗑 清除重选",
        "btn_lbl": "🚀 一键快速导出完美置中商品照片",
        "processing": "⏳ 智慧光学解算中：第 {} 张 / 共 {} 张...",
        "success": "### ✅ 核心解算成功！点数已安全扣除，共生成 {} 张智慧置中照片！",
        "dl_btn": "🎁 点击下载完美置中相片压缩包 (ZIP)",
        "limit_err": "🔒 抱歉，您的免注册试用额度已用完。欢迎在右侧注册登录领取会员免费 20 点，or 立即充值点数套餐包解锁更高生产力！",
        "dup_err": "⚠️ 侦测到重复上传相同照片！框框内不可重复置入相同图档（即使更换档名亦会被安全拦截），请使用清除重选并重新拉入纯净不重复的照片，以防止点数重复扣除争议！",
        "usage_title": "📊 NEXUS CROP 会员钱包看板",
        "guest_info": "🕒 免注册试用钱包：\n* 当日已用点数：**{} / 10** Credits\n* 💡 剩余可用总张数：**{} 张**",
        "welcome": "👋 欢迎回来，尊贵的电商伙伴：**{}** \n* 🪙 免费钱包余额：**{} Credits** (优先扣除)\n* 🪙 付费钱包余额：**{} Credits**\n* 💡 剩余可导出总张数：**{} 张**"
    },
    "English": {
        "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
        "subtitle": "Trading Card & E-commerce Photo Smart Centering, Batch Splitting, and Weight Control System",
        "pricing_html": """
        ### 💰 Choose Your Production Power (Pay-As-You-Go Credits)
        * **🌟 FREE TRIAL**: **$0** (Get **20 Free Credits** upon sign up!) - *Test our heavy-duty centering power.*
        * **🪙 STARTER PACK**: **$4.99** (Get **150 Credits** - *Only $0.033 per perfect photo!*)
        * **⚡ POWER SELLER**: **$19.99** (Get **700 Credits** - *Only $0.028 per perfect photo!*)
        * **👑 MEGA VAULT**: **$49.99** (Get **2,000 Credits** - **Under $0.025 USD per masterpiece!**)
        """,
        "param_header": "⚙️ Layout Ratio & Capacity Parameters (Customizable Values)",
        "ratio_lbl": "Target subject density ratio (10-99%):",
        "size_lbl": "Maximum payload weight constraint per image (MB):",
        "drag_lbl": "📥 DROP ENTIRE IMAGE FOLDER HERE (Inherits original folder names automatically)",
        "loaded_lbl": "📊 Consolidated image queue assets: {} items",
        "clear_btn": "🗑 Clear & Reset Queue",
        "btn_lbl": "🚀 One-Click Quick Export Centered Photos",
        "processing": "⏳ Neural pipeline processing asset {} / {}...",
        "success": "### ✅ Pipeline Render Completed! Credits burned successfully. Total {} assets compiled!",
        "dl_btn": "🎁 Download Centering Assets Package (ZIP)",
        "limit_err": "🔒 Sorry, your anonymous trial quota is exhausted. Please sign up to claim 20 free credits or purchase a token package on the right to unlock more production power!",
        "dup_err": "⚠️ Duplicate photos detected! You cannot upload identical images into the dropzone simultaneously. Please reset queue and upload unique photos to avoid duplicate billing.",
        "usage_title": "📊 PREMIUM WORKSPACE WALLET",
        "guest_info": "🕒 Free Trial Wallet:\n* Daily Used: **{} / 10** Credits\n* 💡 Available Balance: **{} items**",
        "welcome": "👋 Welcome, Premium Partner: **{}** \n* 🪙 Free Credits: **{} Credits** (Prioritized)\n* 🪙 Paid Credits: **{} Credits**\n* 💡 Available Balance: **{} items**"
    },
    "日本語": {
        "title": "🌐 AI 商品画像自動中央配置＆自動クロップシステム",
        "subtitle": "トレカ・EC商品画像の自動クロップ・複数分割・容量と比率の自由設定",
        "pricing_html": """
        ### 💰 プランを選択してください (随時利用可能な Credits トークンパック)
        * **🌟 無料体験**: **$0** (新規登録で **20 無料トークン** プレゼント！) ── *強力な中央配置パワーをお試しください。*
        * **🪙 スターターパック**: **$4.99** ( **150 トークン** 内蔵 ── *画像1枚あたりわずか約5円！*)
        * **⚡ パワーセラーパック**: **$19.99** ( **700 トークン** 内蔵 ── *画像1枚あたりわずか約4.3円！*)
        * **👑 メガバルトパック**: **$49.99** ( **2,000 トークン** 内蔵 ── **圧倒的コスパ：画像1枚あたり4円以下！**)
        """,
        "param_header": "⚙️ 画像比率とファイル容量パラメータ (カスタム数値可能)",
        "ratio_lbl": "出力後の商品主体の表示比率 (10-99%):",
        "size_lbl": "出力画像の最大容量制限 (MB):",
        "drag_lbl": "📥 画像フォルダをここにドラッグ＆ドロップ (フォルダ名を自動的に継承して命名)",
        "loaded_lbl": "📊 読み込まれた画像：{} 枚",
        "clear_btn": "🗑 キューをクリア",
        "btn_lbl": "🚀 ワンクリックで中央配置画像を高速エクスポート",
        "processing": "⏳ 解析中：第 {} 枚 / 全 {} 枚...",
        "success": "### ✅ 解析完了！トークンは正常に消費されました。合計 {} 枚の画像が生成されました！",
        "dl_btn": "🎁 クロップ画像をダウンロード (ZIP)",
        "limit_err": "🔒 申し訳ありませんが、無料お試し枠は終了しました。右側で無料登録して20点を受け取るか、パッケージを購入して生産力を向上させてください！",
        "dup_err": "⚠️ 重複画像が検出されました！同じ写真を複数アップロードすることはできません（ファイル名が異なってもブロックされます）。重複請求を防ぐため、ファイルを整理して再試行してください。",
        "usage_title": "📊 プレミアム会員ウォレット状況",
        "guest_info": "🕒 無料お試し財布:\n* 本日の使用量: **{} / 10** Credits\n* 💡 残り利用可能枚数: **{} 枚**",
        "welcome": "👋 お帰りなさい: **{}** \n* 🪙 無料トークン残量: **{} Credits** (優先消費)\n* 🪙 付費トークン残量: **{} Credits**\n* 💡 残り利用可能枚数: **{} 枚**"
    }
}

st.set_page_config(page_title="NEXUS CROP — AI SaaS", page_icon="🌐", layout="wide")

# 👑 【核心 Python 記憶體指紋狀態機初始化】
if "guest_used_counter" not in st.session_state: st.session_state.guest_used_counter = 0
if "user_authenticated" not in st.session_state: st.session_state.user_authenticated = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "uploader_key_token" not in st.session_state: st.session_state.uploader_key_token = 1000
    # CSS 航太級 3 倍大面積拉圖停機坪注入
st.markdown("""
    <style>
    [data-testid="stFileUploader"] { padding: 35px 0px; }
    [data-testid="stFileUploaderDropzone"] {
        padding: 150px 30px !important;
        border: 3px dashed #3498db !important;
        border-radius: 16px !important;
        background-color: #f8fafc !important;
        transition: all 0.3s ease-in-out;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #2980b9 !important;
        background-color: #f1f5f9 !important;
        box-shadow: 0px 8px 30px rgba(52, 152, 219, 0.25);
    }
    [data-testid="stFileUploaderDropzone"] i {
        transform: scale(2.5) !important;
        margin-bottom: 25px !important;
        color: #3498db !important;
    }
    </style>
""", unsafe_allow_html=True)

lang = st.selectbox("🌐 Language Interface ｜ 多國語言切換晶片", ("繁體中文", "简体中文", "English", "日本語"), index=0)
L = LANG_MAP[lang]

# 👑 👑 👑 【核心 Python 動態餘額實時同步解算大腦】 👑 👑 👑
user_authed = st.session_state.user_authenticated
credits_free = 0
credits_paid = 0
user_uid = ""

if not user_authed:
    current_remaining_quota = max(0, 10 - st.session_state.guest_used_counter)
else:
    if db:
        try:
            user_rec = auth.get_user_by_email(st.session_state.user_email)
            user_uid = user_rec.uid
            user_doc_ref = db.collection("users").document(user_uid)
            user_data = user_doc_ref.get().to_dict()
            credits_free = user_data.get("credits_free", 0)
            credits_paid = user_data.get("credits_paid", 0)
        except:
            credits_free = 20
            credits_paid = 0
    current_remaining_quota = credits_free + credits_paid

# 高級電商雙欄佈局
main_col, side_col = st.columns([0.72, 0.28], gap="large")

with side_col:
    st.markdown(f"### {L['usage_title']}")
    if not user_authed:
        st.info(L["guest_info"].format(st.session_state.guest_used_counter, current_remaining_quota))
        st.markdown("---")
        auth_mode = st.radio("Portal Access", ("Sign In", "Sign Up (Free 20)"), horizontal=True)
        email_in = st.text_input("📧 Email", key="auth_email")
        pass_in = st.text_input("🔒 Password", type="password", key="auth_pass")
        if auth_mode == "Sign Up (Free 20)":
            if st.button("🚀 Establish Account", use_container_width=True):
                try:
                    user = auth.create_user(email=email_in, password=pass_in)
                    if db: db.collection("users").document(user.uid).set({
                        "email": email_in, "credits_free": 20, "credits_paid": 0, "tier": "FREE_TRIAL"
                    })
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
        st.success(L["welcome"].format(st.session_state.user_email, credits_free, credits_paid, current_remaining_quota))
        
        st.markdown("---")
        st.markdown("#### 🪙 Top Up Cloud Wallet")
        if st.button(r"🇺🇸 Starter Pack ($4.99) ── +150 Credits", use_container_width=True, key="side_pack_1"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits_paid": credits_paid + 150})
            st.rerun()
        if st.button(r"🇺🇸 Power Seller ($19.99) ── +700 Credits", use_container_width=True, key="side_pack_2"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits_paid": credits_paid + 700})
            st.rerun()
        if st.button(r"🇺🇸 Mega Vault ($49.99) ── +2000 Credits", use_container_width=True, type="primary", key="side_pack_3"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits_paid": credits_paid + 2000})
            st.rerun()
            
        if st.button("🚪 Sign Out Workspace", use_container_width=True):
            st.session_state.user_authenticated = False
            st.session_state.user_email = ""
            st.rerun()

# 🪐 拼接臨界點：此處開啟 with 閘門，下方第四與第五部分全部精密往右縮排 4 個空格！
with main_col:
    st.title(L["title"])
    st.markdown(f"### *{L['subtitle']}*")
    st.markdown(L["pricing_html"], unsafe_allow_html=True)
    
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

    uploaded_files = st.file_uploader(L["drag_lbl"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"file_uploader_core_{st.session_state.uploader_key_token}")

    # 最前端物理熔斷與 MD5 去重預檢
    num_uploaded = len(uploaded_files) if uploaded_files else 0
    quota_violation = False
    duplicate_violation = False

    if num_uploaded > 0:
        if num_uploaded > current_remaining_quota:
            quota_violation = True
            st.error(L["limit_err"].format(num_uploaded, current_remaining_quota))
        
        seen_hashes = set()
        for f_check in uploaded_files:
            try:
                f_check.seek(0)
                file_hash = hashlib.md5(f_check.read()).hexdigest()
                f_check.seek(0)
                if file_hash in seen_hashes:
                    duplicate_violation = True
                    break
                seen_hashes.add(file_hash)
            except: pass
                
        if duplicate_violation:
            st.error(L["dup_err"])

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(L["clear_btn"], use_container_width=True, key="clear_all_queue"):
            st.session_state.uploader_key_token += 1
            st.session_state.temp_ready = False
            st.rerun()
    with col_btn2:
        # 🔒 雙重安全死鎖：當剩餘可用總張數 <= 0 時，按鈕直接灰色死鎖、完全不給按，高雅提示！
        any_violation = quota_violation or duplicate_violation or (current_remaining_quota <= 0 and num_uploaded == 0)
        start_btn = st.button(L["btn_lbl"], type="primary", use_container_width=True, key="start_pipeline", disabled=any_violation)

    zip_path = "/tmp/processed_centered_images.zip"
    if uploaded_files and not any_violation:
        st.success(L["loaded_lbl"].format(num_uploaded))
        
        if start_btn:
            saved = 0
            progress_bar = st.progress(0)
            status_text = st.empty()
            session = load_rembg_session()
            
            temp_out_dir = "/tmp/processed_centered_images"
            if os.path.exists(temp_out_dir): shutil.rmtree(temp_out_dir)
            if os.path.exists(zip_path): os.remove(zip_path)
            os.makedirs(temp_out_dir, exist_ok=True)
            
            for idx, file in enumerate(uploaded_files, 1):
                status_text.markdown(L["processing"].format(idx, num_uploaded))
                try:
                    folder_prefix = ""
                    file_raw_name = getattr(file, "name", "photo.jpg")
                    
                    if hasattr(file, "path"):
                        raw_path_str = file.path
                        path_parts = raw_path_str.replace("\\", "/").split("/")
                        if len(path_parts) > 1:
                            folder_prefix = f"[{path_parts[-2]}]_"
                    elif hasattr(file, "webkitRelativePath") and file.webkitRelativePath:
                        raw_path_str = file.webkitRelativePath
                        path_parts = raw_path_str.replace("\\", "/").split("/")
                        if len(path_parts) > 1:
                            folder_prefix = f"[{path_parts[-2]}]_"
                    
                    file.seek(0)
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
                    
                    if not valid_boxes: valid_boxes.append((int(w*0.25), int(h*0.25), int(w*0.5), int(w*0.5)))
                    
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
                        
                        base_name, _ = os.path.splitext(file_raw_name)
                        if len(valid_boxes) > 1:
                            out_img_name = f"{folder_prefix}{base_name}_置中裁剪_{part_idx}.jpg"
                        else:
                            out_img_name = f"{folder_prefix}{base_name}_置中裁剪.jpg"
                            
                        with open(os.path.join(temp_out_dir, out_img_name), "wb") as f_out: f_out.write(buf.tobytes())
                        saved += 1
                        
                    del img, img_orig, img_rotated, contours_normal, contours_rotated; gc.collect()
                except Exception as e: st.error(f"Error {file_raw_name}: {str(e)}")
                progress_bar.progress(idx / num_uploaded)
            
            if saved > 0:
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for root, _, files in os.walk(temp_out_dir):
                        for f in files: zip_file.write(os.path.join(root, f), f)
                
                # 👑 👑 👑 【純 Python 記憶體現場立刻扣點！】 👑 👑 👑
                if not user_authed:
                    st.session_state.guest_used_counter += num_uploaded
                else:
                    if credits_free >= num_uploaded:
                        new_free = credits_free - num_uploaded
                        new_paid = credits_paid
                    else:
                        remainder = num_uploaded - credits_free
                        new_free = 0
                        new_paid = max(0, credits_paid - remainder)
                    if db and user_uid:
                        db.collection("users").document(user_uid).update({
                            "credits_free": new_free, "credits_paid": new_paid
                        })
                
                st.session_state.compiled_saved = saved
                st.session_state.temp_ready = True
                st.success(L["success"].format(saved))
                st.rerun()
                
        if "temp_ready" in st.session_state and st.session_state.temp_ready and os.path.exists(zip_path):
            zip_file_size = os.path.getsize(zip_path)
            if zip_file_size > 0:
                with open(zip_path, "rb") as f_zip:
                    zip_data = f_zip.read()
                
                if st.download_button(label=L["dl_btn"], data=zip_data, file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True, key="dl_zip_btn_final_gate"):
                    st.session_state.uploader_key_token += 1
                    st.session_state.temp_ready = False
                    st.rerun()
