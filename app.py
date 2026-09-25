import os, io, zipfile, cv2, gc, shutil, numpy as np
from PIL import Image
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth

# 👑 Firebase 雲端保險箱連線晶片 (從 Streamlit Secrets 安全隱形讀取)
if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        pass

db = firestore.client() if firebase_admin._apps else None

# 👑 雲端快取優化：確保 AI 模型在雲端唯一下載一次
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

# 🌍 跨國網拍 SaaS 8 國語言大字典 (A面：英文、繁中、日文、簡中)
LANG_MAP = {
    "English": {
        "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
        "subtitle": "Enterprise E-commerce Photo Pipeline (Standby)",
        "param_header": "⚙️ AI Optimization & Parameter Infrastructure (Keyboard input enabled)",
        "ratio_lbl": "Target subject density ratio (10-99%):",
        "size_lbl": "Maximum payload weight constraint per image (MB):",
        "tip_header": "💡 FREE OPERATIONAL SPECIFICATIONS",
        "tip_body": "1. Directly type your parameters below via keyboard.\n2. Drag single images or folder into the drop zone.\n3. Click the button to initialize the neural pipeline for FREE!\n4. Sign up or unlock packages below to download your processed ZIP.",
        "drag_lbl": "📥 DROP IMAGES HERE FOR FREE NEURAL CENTERING",
        "loaded_lbl": "📊 Consolidated image queue assets: {} items",
        "clear_btn": "🗑 Clear & Reset Queue",
        "btn_lbl": "🚀 One-Click Batch Export Centered Photos",
        "processing": "⏳ Neural pipeline processing asset {} / {}...",
        "success": "### ✅ Pipeline Render Completed! Total {} assets compiled in cloud disk!",
        "dl_btn": "🎁 Unlock & Download Centering Assets Package (ZIP)",
        "limit_err": "🔒 DEPLOYMENT PACK LOCKED ── Free trial quota cap exceeded (Max 10 Credits/24H). Please sign in or purchase token packages below to unlock high-res ZIP package immediately.",
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
        "limit_err": "🔒 相片打包已安全鎖死 ── 免註冊試用額度（每天限 10 Credits）已用完！請在右側註冊登入，或充值點數套餐，即可立刻全速下載您改好的高畫質 ZIP 壓縮檔！",
        "usage_title": "📊 NEXUS CROP 會員錢包看板",
        "welcome": "👋 歡迎回來，尊貴的電商夥伴：**{}** ｜ 🪙 專屬錢包餘額：**{} Credits**"
    },
    "日本語": {
        "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
        "subtitle": "Enterprise E-commerce Photo Pipeline (Standby)",
        "param_header": "⚙️ AI最適化パラメータ設定 (キーボード手動入力対応)",
        "ratio_lbl": "出力後の商品主体の表示比率 (10-99%):",
        "size_lbl": "出力画像の最大容量制限 (MB):",
        "tip_header": "💡 操作仕様説明 (無料体験実施中)",
        "tip_body": "1. ボックスをクリックして数値を入力してください。\n2. 画像またはフォルダを下のボックスにドラッグ＆ドロップしてください。\n3. ボタンをクリックすると、無料でクラウド解析が開始されます。\n4. 解析完了後、ログインまたはトークンを購入してダウンロードしてください。",
        "drag_lbl": "📥 画像またはフォルダをここにドラッグ＆ドロップ (無料トライアル、大量一括処理対応)",
        "loaded_lbl": "📊 読み込まれた画像：{} 枚",
        "clear_btn": "🗑 キューをクリア",
        "btn_lbl": "🚀 One-Click Batch Export Centered Photos",
        "processing": "⏳ 解析中：第 {} 枚 / 全 {} 枚...",
        "success": "### ✅ 解析完了！合計 {} 枚の画像がクラウドで生成されました！",
        "dl_btn": "🎁 パッケージを解鎖してダウンロード (ZIP)",
        "limit_err": "🔒 パッケージがロックされました ── 無料枠制限(1日10 Creditsまで)を超えました。右側でログインするか、トークンを購入してダウンロードしてください。",
        "usage_title": "📊 プレミアム会員ウォレット状況",
        "welcome": "👋 お帰りなさい、プレミアムパートナー: **{}** ｜ 🪙 残りトークン: **{} Credits**"
    },
    "简体中文": {
        "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
        "subtitle": "Enterprise E-commerce Photo Pipeline (Standby)",
        "param_header": "⚙️ 最速电商智慧识别参数设置 (支持键盘手动自行输入)",
        "ratio_lbl": "导出后主体占画面比例 (10-99%):",
        "size_lbl": "导出后照片档最大容量限制 (MB):",
        "tip_header": "💡 商品智慧置中系统说明 (免费开放体验中)",
        "tip_body": "1. 点击下方输入框，可直接用键盘手动自行打字输入置中比例数值。\n2. 可以将单张图片或整个图片文件夹直接全数拖拽至下方巨型向量场中。\n3. 按下秒级导出按钮即可全自动免费解算！\n4. 画面显示成功生成后，登录您的云端钱包或充值点数包即可立刻带走高画质相片包！",
        "drag_lbl": "📥 将单张相片或整个图片文件夹全数拖拽至此（免注册直接免费体验，25张大文件通杀）",
        "loaded_lbl": "📊 目前已载入商品照片：{} 张",
        "clear_btn": "🗑 清除重选",
        "btn_lbl": "🚀 One-Click Batch Export Centered Photos",
        "processing": "⏳ 智慧光学解算中：第 {} 张 / 共 {} 张...",
        "success": "### ✅ 核心解算成功！共生成 {} 张智慧置中照片！",
        "dl_btn": "🎁 点击解锁并下载完美置中相片压缩包 (ZIP)",
        "limit_err": "🔒 相片打包已安全锁死 ── 免注册试用额度（每天限 10 Credits）已用完！请在右侧注册登录，或充值点数套餐，即可立刻全速下载您改好的高画质 ZIP 压缩档！",
        "usage_title": "📊 NEXUS CROP 会员钱包看板",
        "welcome": "👋 欢迎回来，尊贵的电商伙伴：**{}** ｜ 🪙 专属钱包余额：**{} Credits**"
    },
    "한국어": {
        "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
        "subtitle": "Enterprise E-commerce Photo Pipeline (Standby)",
        "param_header": "⚙️ AI 최적화 및 매개변수 설정 (키보드 입력 가능)",
        "ratio_lbl": "출력 후 객체 화면 비율 (10-99%):",
        "size_lbl": "출력 이미지 최대 용량 제한 (MB):",
        "tip_header": "💡 무료 작업 사양 가이드",
        "tip_body": "1. 입력 상자를 클릭하여 키보드로 직접 수치를 입력하세요.\n2. 단일 이미지 또는 이미지 폴더를 아래 영역으로 드래그 하세요.\n3. 버튼을 클릭하면 클라우드 분석이 무상으로 시작됩니다.\n4. 완료 후 로그인하거나 토큰을 구매하여 다운로드하세요.",
        "drag_lbl": "📥 이미지 또는 폴더를 여기에 드래그 앤 드롭 (무료 체험, 대량 파일 지원)",
        "loaded_lbl": "📊 로드된 상품 이미지: {} 장",
        "clear_btn": "🗑 대기열 비우기",
        "btn_lbl": "🚀 One-Click Batch Export Centered Photos",
        "processing": "⏳ 분석 중: {} / {} 번째 이미지 처리 중...",
        "success": "### ✅ 분석 완료! 총 {} 장의 이미지가 클라우드 디스크에 생성되었습니다!",
        "dl_btn": "🎁 패키지 잠금 해제 및 다운로드 (ZIP)",
        "limit_err": "🔒 다운로드 패키지 잠김 ── 무료 체험 한도(일일 10 Credits)를 초과했습니다. 오른쪽에서 로그인하거나 토큰을 구매하여 다운로드하세요.",
        "usage_title": "📊 프리미엄 회원 지갑 상태",
        "welcome": "👋 어서 오세요, 프리미엄 파트너: **{}** ｜ 🪙 잔여 토큰: **{} Credits**"
    },
    "ภาษาไทย": {
        "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
        "subtitle": "Enterprise E-commerce Photo Pipeline (Standby)",
        "param_header": "⚙️ การตั้งค่าพารามิเตอร์ AI (รองรับการพิมพ์ด้วยคีย์บอร์ด)",
        "ratio_lbl": "สัดส่วนของสินค้าในภาพ (10-99%):",
        "size_lbl": "จำกัดขนาดไฟล์สูงสุด (MB):",
        "tip_header": "💡 คำแนะนำการใช้งานฟรี",
        "tip_body": "1. คลิกช่องด้านล่างและพิมพ์ตัวเลขด้วยคีย์บอร์ดได้โดยตรง\n2. ลากไฟล์รูปภาพหรือโฟลเดอร์ทั้งหมดมาวางในช่องด้านล่าง\n3. คลิกปุ่มเพื่อเริ่มประมวลผลบนระบบคลาวด์ฟรีทันที!\n4. เมื่อเสร็จสิ้น เข้าสู่ระบบหรือซื้อแพ็กเกจโทเค็นเพื่อดาวน์โหลดไฟล์ ZIP",
        "drag_lbl": "📥 ลากรูปภาพหรือโฟลเดอร์มาวางที่นี่ (ทดลองใช้ฟรี รองรับการประมวลผลจำนวนมาก)",
        "loaded_lbl": "📊 รูปภาพที่โหลดสำเร็จ: {} ภาพ",
        "clear_btn": "🗑 ล้างคิวรูปภาพ",
        "btn_lbl": "🚀 One-Click Batch Export Centered Photos",
        "processing": "⏳ กำลังประมวลผลภาพที่ {} / {}...",
        "success": "### ✅ ประมวลผลเสร็จสิ้น! สร้างรูปภาพทั้งหมด {} ภาพบนดิสก์คลาวด์เรียบร้อย!",
        "dl_btn": "🎁 ปลดล็อกและดาวน์โหลดไฟล์ ZIP",
        "limit_err": "🔒 แฟ้มดาวน์โหลดถูกล็อก ── คุณใช้โควต้าทดลองใช้ฟรีเกินกำหนดแล้ว (สูงสุด 10 Credits/24 ชม.) กรุณาเข้าสู่ระบบหรือซื้อโทเค็นเพิ่มที่ด้านขวาเพื่อดาวน์โหลดไฟล์ ZIP ความละเอียดสูงทันที",
        "usage_title": "📊 สถานะกระเป๋าเงินสมาชิกพรีเมียม",
        "welcome": "👋 ยินดีต้อนรับสมาชิกพรีเมียม: **{}** ｜ 🪙 โทเค็นคงเหลือ: **{} Credits**"
    },
    "Bahasa Melayu": {
        "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
        "subtitle": "Enterprise E-commerce Photo Pipeline (Standby)",
        "param_header": "⚙️ Infrastruktur Parameter & Optimasi AI (Input papan kekunci didayakan)",
        "ratio_lbl": "Nisbah kepadatan subjek sasaran (10-99%):",
        "size_lbl": "Had saiz fail maksimum per imej (MB):",
        "tip_header": "💡 SPESIFIKASI OPERASI PERCUMA",
        "tip_body": "1. Taip parameter optimasi anda secara langsung di bawah melalui papan kekunci.\n2. Seret imej tunggal atau folder ke dalam zon digugurkan di bawah.\n3. Klik fungsi butang untuk memulakan saluran paip render neural secara PERCUMA!\n4. Log masuk atau buka kunci pakej token di bawah untuk memuat turun muatan ZIP.",
        "drag_lbl": "📥 GUGURKAN IMEJ TUNGGAL ATAU FOLDER DI SINI UNTUK SMART CENTERING PERCUMA",
        "loaded_lbl": "📊 Aset imej terkumpul: {} item",
        "clear_btn": "🗑 Padam & Set Semula",
        "btn_lbl": "🚀 One-Click Batch Export Centered Photos",
        "processing": "⏳ Saluran paip neural memproses aset {} / {}...",
        "success": "### ✅ Proses Selesai! Sebanyak {} aset telah dijana di dalam cakera awan!",
        "dl_btn": "🎁 Buka Kunci & Muat Turun Pakej ZIP",
        "limit_err": "🔒 PAKEJ DIKUNCI ── Had pelan percuma telah melebihi (Maks 10 Credits/24H). Sila log masuk atau beli pakej token di bawah untuk memuat turun fail ZIP resolusi tinggi dengan segera.",
        "usage_title": "📊 STATUS DOMPET PREMIUM SAAS",
        "welcome": "👋 Selamat kembali, Rakan Premium: **{}** ｜ 🪙 Baki Dompet Awam: **{} Credits**"
    },
    "Bahasa Indonesia": {
        "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
        "subtitle": "Enterprise E-commerce Photo Pipeline (Standby)",
        "param_header": "⚙️ Optimasi AI & Konfigurasi Parameter (Mendukung input keyboard)",
        "ratio_lbl": "Rasio kepadatan subjek target (10-99%):",
        "size_lbl": "Batas kapasitas ukuran file maksimum per gambar (MB):",
        "tip_header": "💡 SPESIFIKASI OPERASIONAL GRATIS",
        "tip_body": "1. Ketik nilai parameter pengoptimalan Anda langsung di bawah menggunakan keyboard.\n2. Seret gambar tunggal atau seluruh folder ke dalam kotak drop zone di bawah.\n3. Klik tombol eksekusi untuk memulai rendering AI secara GRATIS!\n4. Masuk ke akun Anda atau beli paket token di bawah untuk mengunduh paket file ZIP.",
        "drag_lbl": "📥 SERET GAMBAR TUNGGAL ATAU FOLDER DI SINI UNTUK SMART CENTERING GRATIS",
        "loaded_lbl": "📊 Total aset gambar yang dimuat: {} item",
        "clear_btn": "🗑 Bersihkan Antrean",
        "btn_lbl": "🚀 One-Click Batch Export Centered Photos",
        "processing": "⏳ Sistem AI sedang memproses aset gambar {} / {}...",
        "success": "### ✅ Proses AI Selesai! Sebanyak {} aset gambar berhasil dibuat di disk cloud!",
        "dl_btn": "🎁 Buka Kunci & Unduh Paket ZIP",
        "limit_err": "🔒 PAKET DOWNLOAD DIKUNCI ── Kuota uji coba gratis Anda telah habis (Maks 10 Credits/24 jam). Silakan masuk ke akun atau beli paket token di bawah untuk mengunduh file ZIP resolusi tinggi segera.",
        "usage_title": "📊 STATUS DOMPET PREMIUM ANGGOTA",
        "welcome": "👋 Selamat datang kembali, Mitra Premium: **{}** ｜ 🪙 Sisa Token Dompet Cloud: **{} Credits**"
    }
}

st.set_page_config(page_title="NEXUS CROP — AI SaaS", page_icon="🌐", layout="wide")

# 👑 【免註冊遊客 24小時限額 10 Credits 狀態機初始化】
if "daily_usage" not in st.session_state:
    st.session_state.daily_usage = 0
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
    # 🪐 點亮頂級 8 國語言切換晶片 (一指秒級全面換膚切換)
lang = st.selectbox("🌐 Language Interface ｜ 多國語言切換晶片", ("English", "繁體中文", "日本語", "简体中文", "한국어", "ภาษาไทย", "Bahasa Melayu", "Bahasa Indonesia"), index=0)
L = LANG_MAP[lang]

# 👑 全球高級電商雙欄位大氣佈局：左邊放無阻礙核心功能，右邊放 Firebase 會員控制與充值看板
main_col, side_col = st.columns([3, 1], gap="large")

with side_col:
    st.markdown(f"### {L['usage_title']}")
    if not st.session_state.user_authenticated:
        # 📊 免註冊用戶，右側即時秀出他今天剩幾張免費額度，拉高焦慮感促使註冊！
        st.info(f"🕒 Unregistered Free Tier:\n* Daily Used: **{st.session_state.daily_usage} / 10** Credits\n*(Resets every 24 hours)*")
        st.markdown("---")
        auth_mode = st.radio("Portal Access", ("Sign In", "Sign Up (Free 20)"), horizontal=True)
        email_in = st.text_input("📧 Email", key="auth_email")
        pass_in = st.text_input("🔒 Password", type="password", key="auth_pass")
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
        
        # 🪙 點數充值套餐 (與主面板話術 100% 絕對完全對齊！)
        st.markdown("---")
        st.markdown("#### 🪙 Top Up Cloud Wallet")
        if st.button("🇺🇸 Starter Pack (\$4.99) ── +150 Credits", use_container_width=True, key="side_pack_1"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits": current_credits + 150})
            st.rerun()
        if st.button("🇺🇸 Power Seller (\$19.99) ── +700 Credits", use_container_width=True, key="side_pack_2"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits": current_credits + 700})
            st.rerun()
        if st.button("🇺🇸 Mega Vault (\$49.99) ── +2000 Credits", use_container_width=True, type="primary", key="side_pack_3"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits": current_credits + 2000})
            st.rerun()
            
        if st.button("🚪 Sign Out Workspace", use_container_width=True):
            st.session_state.user_authenticated = False
            st.session_state.user_email = ""
            st.rerun()

with main_col:
    # 👑 100% 灌入您指定的頂級高端歐美 SaaS 標題與「4層按張計費點數包」對照話術文字
    st.title(L["title"])
    st.markdown(f"### *{L['subtitle']}*")
    
    st.markdown("""
    ### 💰 Choose Your Production Power (Pay-As-You-Go Credits)
    * **🌟 FREE TRIAL**: **$0** (Get **20 Free Credits** upon sign up!) - *Test our heavy-duty centering power.*
    * **🪙 STARTER PACK**: **$4.99** (Get **150 Credits** - *Only $0.033 per perfect photo!*)
    * **⚡ POWER SELLER**: **$19.99** (Get **700 Credits** - *Only $0.028 per perfect photo!*)
    * **👑 MEGA VAULT**: **$49.99** (Get **2,000 Credits** - **Under $0.025 USD per masterpiece!**)
    """)
    
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

    uploaded_files = st.file_uploader(L["drag_lbl"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(L["clear_btn"], use_container_width=True, key="clear_all_queue"):
            st.rerun()
    with col_btn2:
        start_btn = st.button(L["btn_lbl"], type="primary", use_container_width=True, key="start_pipeline")

    if uploaded_files:
        st.success(L["loaded_lbl"].format(len(uploaded_files)))
        
        # 👑 大方放行，允許任何遊客直接在硬碟免費跑完去背與置中裁切進度條！
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
                
        # 👑 👑 👑 【1原圖扣1點：一鍵下載時精準比對原始上傳張數！】 👑 👑 👑
        if "temp_ready" in st.session_state and st.session_state.temp_ready:
            zip_path = "/tmp/processed_centered_images.zip"
            if not os.path.exists(zip_path):
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for root, _, files in os.walk("/tmp/processed_centered_images"):
                        for f in files: zip_file.write(os.path.join(root, f), f)
                        
            user_authed = st.session_state.user_authenticated
            user_credits_val = current_credits if (user_authed and 'current_credits' in locals()) else 0
            
            # 🔒 雙軌安全大閘門 (精準按照原始上傳原圖張數計算)
            if not user_authed:
                if st.session_state.daily_usage + len(uploaded_files) > 10:
                    st.error(L["limit_err"])
                else:
                    with open(zip_path, "rb") as f_zip:
                        if st.download_button(label=L["dl_btn"], data=f_zip.read(), file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True, key="dl_zip_btn_guest"):
                            st.session_state.daily_usage += len(uploaded_files)
                            st.session_state.temp_ready = False
                            st.rerun()
            else:
                if user_credits_val < len(uploaded_files):
                    st.error(L["limit_err"])
                else:
                    with open(zip_path, "rb") as f_zip:
                        if st.download_button(label=L["dl_btn"], data=f_zip.read(), file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True, key="dl_zip_btn_user"):
                            new_balance = max(0, user_credits_val - len(uploaded_files))
                            if db and user_uid:
                                db.collection("users").document(user_uid).update({"credits": new_balance})
                            st.session_state.temp_ready = False
                            st.rerun()
