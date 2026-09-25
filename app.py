import os, io, zipfile, cv2, gc, shutil, numpy as np
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

# 👑 雲端快取優化：確保 AI 去背模型在雲端唯一下載一次
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

# 🌍 跨國網拍 SaaS 8 國語言大字典 (A面：繁中、簡中、英文、日文)
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
        "drag_lbl": "📥 將「單張相片」或「整個圖片資料夾」全數拖曳至此（超巨型拖曳停機坪，免註冊免費體驗，25張大文件通殺）",
        "loaded_lbl": "📊 目前已載入商品照片：{} 張",
        "clear_btn": "🗑 清除重選",
        "btn_lbl": "🚀 一鍵快速導出完美置中商品照片",
        "processing": "⏳ 智慧光學解算中：第 {} 張 / 共 {} 張...",
        "success": "### ✅ 核心解算成功！共生成 {} 張智慧置中照片！",
        "dl_btn": "🎁 點擊解鎖並下載完美置中相片壓縮包 (ZIP)",
        "limit_err": "❌ 額度攔截熔斷！本批上傳商品照量（{}張）大於您的剩餘可用點數（{}點）。請使用左側清除重選按鈕減少照片上傳量，或立即在右側登入/充值點數套餐包！",
        "usage_title": "📊 NEXUS CROP 會員錢包看板",
        "guest_info": "🕒 免註冊試用錢包：\n* 當日已用點數：**{} / 10** Credits (每24小時全自動重置歸零)\n* 30日累計使用：**{} / 30** Credits\n* 💡 剩餘可導出總張數：**{} 張**",
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
        "size_lbl": "导出后照片档最大容量限制 (MB):",
        "drag_lbl": "📥 将单张相片 or 整个图片文件夹全数拖拽至此（超巨型拖拽停机坪，免注册免费体验，25张大文件通杀）",
        "loaded_lbl": "📊 目前已载入商品照片：{} 张",
        "clear_btn": "🗑 清除重选",
        "btn_lbl": "🚀 一键快速导出完美置中商品照片",
        "processing": "⏳ 智慧光学解算中：第 {} 张 / 共 {} 张...",
        "success": "### ✅ 核心解算成功！共生成 {} 张智慧置中照片！",
        "dl_btn": "🎁 点击解锁并下载完美置中相片压缩包 (ZIP)",
        "limit_err": "❌ 额度拦截熔断！本批上传商品照量（{}张）大于您的剩余可用点数（{}点）。请使用左侧清除重选按钮减少照片上传量，or 立即在右侧登录/充值点数套餐包！",
        "usage_title": "📊 NEXUS CROP 会员钱包看板",
        "guest_info": "🕒 免注册试用钱包：\n* 当日已用点数：**{} / 10** Credits (每24小时全自动重置归零)\n* 30日累计使用：**{} / 30** Credits\n* 💡 剩余可导出总张数：**{} 张**",
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
        "drag_lbl": "📥 DROP SINGLE IMAGES OR ENTIRE IMAGE FOLDER HERE FOR FREE NEURAL CENTERING",
        "loaded_lbl": "📊 Consolidated image queue assets: {} items",
        "clear_btn": "🗑 Clear & Reset Queue",
        "btn_lbl": "🚀 One-Click Quick Export Centered Photos",
        "processing": "⏳ Neural pipeline processing asset {} / {}...",
        "success": "### ✅ Pipeline Render Completed! Total {} assets compiled in cloud disk!",
        "dl_btn": "🎁 Unlock & Download Centering Assets Package (ZIP)",
        "limit_err": "❌ Quota Pre-validation Refused! Your batch payload ({} assets) exceeds your active workspace credits ({} items). Please clear queue to reduce your size, or purchase token packages right now.",
        "usage_title": "📊 PREMIUM WORKSPACE WALLET",
        "guest_info": "🕒 Unregistered Free Tier:\n* Daily Used: **{} / 10** Credits (Resets every 24H)\n* 30-Day Total Used: **{} / 30** Credits\n* 💡 Available Balance: **{} items**",
        "welcome": "👋 Welcome, Premium Partner: **{}** \n* 🪙 Free Credits: **{} Credits** (Prioritized)\n* 🪙 Paid Credits: **{} Credits**\n* 💡 Available Balance: **{} items**"
    },
    "日本語": {
        "title": "🌐 AI 商品画像自動中央配置＆自動クロップシステム",
        "subtitle": "トレカ・EC商品画像の自動クロップ・複数分割・容量と比率의自由設定",
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
        "drag_lbl": "📥 画像またはフォルダをここにドラッグ＆ドロップ (超巨大ドロップゾーン、無料トライアル対応)",
        "loaded_lbl": "📊 読み込まれた画像：{} 枚",
        "clear_btn": "🗑 キューをクリア",
        "btn_lbl": "🚀 ワンクリックで中央配置画像を高速エクスポート",
        "processing": "⏳ 解析中：第 {} 枚 / 全 {} 枚...",
        "success": "### ✅ 解析完了！合計 {} 枚 of 画像がクラウドで生成されました！",
        "dl_btn": "🎁 パッケージを解鎖してダウンロード (ZIP)",
        "limit_err": "❌ 利用制限インターセプト！アップロードされた画像（{}枚）が残りのトークン枠（{}枚）を超えています。アップロード数を減らすか、トークンを即時購入してください。",
        "usage_title": "📊 プレミアム会員ウォレット状況",
        "guest_info": "🕒 未登録の無料プラン:\n* 本日の使用量: **{} / 10** Credits (24時間リセット)\n* 30日間の累計使用量: **{} / 30** Credits\n* 💡 残り利用可能枚数: **{} 枚**",
        "welcome": "👋 お帰りなさい: **{}** \n* 🪙 無料トークン残量: **{} Credits** (優先消費)\n* 🪙 付費トークン残量: **{} Credits**\n* 💡 残り利用可能枚数: **{} 枚**"
    },
    "한국어": {
        "title": "🌐 AI 이커머스 상품 이미지 자동 중앙 배치 시스템",
        "subtitle": "트레이딩 카드 및 쇼핑몰 상품 이미지 크롭, 다중 분할 및 비율 용량 자유 설정",
        "pricing_html": """
        ### 💰 요금제 선택 (충전식 Credits 토큰 팩)
        * **🌟 무료 체험**: **$0** (가입 시 **20 무료 토큰** 즉시 지급!) ── *강력한 중앙 정렬 시스템을 테스트해 보세요.*
        * **🪙 스타터 팩**: **$4.99** ( **150 토큰** 포함 ── *이미지 장당 단돈 약 45원!*)
        * **⚡ 파워 셀러 팩**: **$19.99** ( **700 토큰** 포함 ── *이미지 장당 단돈 약 38원!*)
        * **👑 메가 볼트 팩**: **$49.99** ( **2,000 토큰** 포함 ── **최고의 가성비: 이미지 장당 34원 이하!**)
        """,
        "param_header": "⚙️ 배치 비율 및 파일 용량 매개변수 (값 자율 지정 가능)",
        "ratio_lbl": "출력 후 객체 화면 비율 (10-99%):",
        "size_lbl": "출력 이미지 최대 용량 제한 (MB):",
        "drag_lbl": "📥 이미지 또는 폴더를 여기에 드래그 앤 드롭 (초대형 드롭존, 무료 체험 지원)",
        "loaded_lbl": "📊 로드된 상품 이미지: {} 장",
        "clear_btn": "🗑 대기열 비우기",
        "btn_lbl": "🚀 원클릭 일괄 중앙 배치 이미지 신속 내보내기",
        "processing": "⏳ 분석 중: {} / {} 번째 이미지 처리 중...",
        "success": "### ✅ 분석 완료! 총 {} 장의 이미지가 클라우드 디스크에 생성되었습니다!",
        "dl_btn": "🎁 패키지 잠금 해제 및 다운로드 (ZIP)",
        "limit_err": "❌ 한도 사전 차단! 요청된 파일 장수（{}장）가 잔여 한도（{}장）를 초과했습니다. 업로드 개수를 줄이거나 오른쪽에서 토큰을 즉시 구매하세요.",
        "usage_title": "📊 프리미엄 회원 지갑 상태",
        "guest_info": "🕒 비회원 무료 지갑:\n* 금일 사용량: **{} / 10** Credits (24시간 리셋)\n* 30일 누적 사용량: **{} / 30** Credits\n* 💡 남은 이용 가능 장수: **{} 장**",
        "welcome": "👋 어서 오세요, 프리미엄 파트너: **{}** \n* 🪙 무료 토큰 잔액: **{} Credits** (우선 차감)\n* 🪙 유료 토큰 잔액: **{} Credits**\n* 💡 남은 이용 가능 장수: **{} 장**"
    },
    "ภาษาไทย": {
        "title": "🌐 AI ระบบจัดจุดกึ่งกลางภาพสินค้าอีคอมเมิร์ซอัตโนมัติ",
        "subtitle": "ระบบครอปภาพสินค้า แยกหลายภาพ จัดกึ่งกลาง และตั้งค่าขนาดไฟล์ตามใจชอบ (พร้อมใช้งาน)",
        "pricing_html": """
        ### 💰 เลือกแพ็กเกจการผลิตของคุณ (แพ็กเกจเติมโทเค็น Credits)
        * **🌟 ทดลองใช้ฟรี**: **$0** (สมัครสมาชิกรับฟรี **20 โทเค็น**!) ── *ทดสอบระบบจัดจุดกึ่งกลางภาพอัจฉริยะของเรา*
        * **🪙 แพ็กเกจเริ่มต้น**: **$4.99** (รับ **150 โทเค็น** ── *เฉลี่ยเพียงภาพละ 1.1 บาทเท่านั้น!*)
        * **⚡ แพ็กเกจแม่ค้ามือโปร**: **$19.99** (รับ **700 โทเค็น** ── *เฉลี่ยเพียงภาพละ 0.9 บาทเท่านั้น!*)
        * **👑 แพ็กเกจมหาเศรษฐีข้ามพรมแดน**: **$49.99** (รับ **2,000 โทเค็น** ── **คุ้มค่าที่สุด: เฉลี่ยภาพละไม่ถึง 0.8 บาท!**)
        """,
        "param_header": "⚙️ พารามิเตอร์สัดส่วนและขนาดไฟล์ภาพ (ระบุค่าได้เอง)",
        "ratio_lbl": "สัดส่วนของสินค้าสินค้าในภาพ (10-99%):",
        "size_lbl": "จำกัดขนาดไฟล์สูงสุด (MB):",
        "drag_lbl": "📥 ลากรูปภาพหรือโฟลเดอร์มาวางที่นี่ (ทดลองใช้ฟรี ไม่ต้องลงทะเบียน)",
        "loaded_lbl": "📊 รูปภาพที่โหลดสำเร็จ: {} ภาพ",
        "clear_btn": "🗑 ล้างคิวรูปภาพ",
        "btn_lbl": "🚀 ส่งออกรูปภาพจัดกึ่งกลางอัตโนมัติอย่างรวดเร็วในคลิกเดียว",
        "processing": "⏳ กำลังประมวลผลภาพที่ {} / {}...",
        "success": "### ✅ ประมวลผลเสร็จสิ้น! สร้างรูปภาพทั้งหมด {} ภาพบนดิสก์คลาวด์เรียบร้อย!",
        "dl_btn": "🎁 ปลดล็อกและดาวน์โหลดไฟล์ ZIP",
        "limit_err": "🔒 ระบบระงับโควต้าล่วงหน้า! รูปภาพที่อัปโหลด ({}ภาพ) เกินโควต้าคงเหลือของคุณ ({}ภาพ) กรุณาลดจำนวนรูปภาพลงหรือเติมเงินซื้อโทเค็นด้านขวา",
        "usage_title": "📊 สถานะกระเป๋าเงินสมาชิกพรีเมียม",
        "guest_info": "🕒 กระเป๋าเงินทดลองใช้ฟรี:\n* ใช้งานวันนี้แล้ว: **{} / 10** Credits (รีเซ็ตทุก 24 ชม.)\n* สะสม 30 วัน: **{} / 30** Credits\n* 💡 จำนวนภาพที่ประมวลผลได้เหลือ: **{} ภาพ**",
        "welcome": "👋 ยินดีต้อนรับสมาชิกพรีเมียม: **{}** \n* 🪙 โทเค็นฟรีคงเหลือ: **{} Credits** (หักก่อน)\n* 🪙 โทเค็นเติมเงินคงเหลือ: **{} Credits**\n* 💡 จำนวนภาพที่ประมวลผลได้เหลือ: **{} ภาพ**"
    },
    "Bahasa Melayu": {
        "title": "🌐 AI Sistem Centering & Pemotongan Gambar E-dagang",
        "subtitle": "Pemotongan Automatik, Pengasingan Gambar Pukal, dan Tetapan Bebas Saiz Fail (Sedia)",
        "pricing_html": """
        ### 💰 Pilih Pakej Kuasa Pengeluaran Anda (Pakej Kredit Token)
        * **🌟 PERCUBAAN PERCUMA**: **$0** (Daftar dapat **20 Kredit Percuma**!) ── *Uji sistem smart centering kami.*
        * **🪙 PAKEJ PERMULAAN**: **$4.99** (Dapat **150 Kredit** ── *Hanya sekitar RM0.15 bagi setiap gambar yang sempurna!*)
        * **⚡ PAKEJ PENJUAL AKTIF**: **$19.99** (Dapat **700 Kredit** ── *Hanya sekitar RM0.13 bagi setiap gambar yang sempurna!*)
        * **👑 PAKEJ GERGASI E-DAGANG**: **$49.99** (Dapat **2,000 Kredit** ── **Nilai Hebat: Di bawah RM0.11 bagi setiap gambar!**)
        """,
        "param_header": "⚙️ Parameter Nisbah & Kapasiti Fail (Nilai Boleh Diubahsuai)",
        "ratio_lbl": "Nisbah kepadatan subjek sasaran (10-99%):",
        "size_lbl": "Had saiz fail maksimum per imej (MB):",
        "drag_lbl": "📥 GUGURKAN IMEJ TUNGGAL ATAU FOLDER DI SINI (Zon Drop Gergasi, Percubaan Percuma Didayakan)",
        "loaded_lbl": "📊 Aset imej terkumpul: {} item",
        "clear_btn": "🗑 Padam & Set Semula",
        "btn_lbl": "🚀 Eksport Gambar Centered Secara Pukal Pantas Satu-Klik",
        "processing": "⏳ Saluran paip neural memproses aset {} / {}...",
        "success": "### ✅ Proses Selesai! Sebanyak {} aset telah dijana di dalam cakera awan!",
        "dl_btn": "🎁 Buka Kunci & Muat Turun Pakej ZIP",
        "limit_err": "🔒 Sekatan Kuota Awal! Muatan gambar anda ({} item) melebihi baki kredit semasa anda ({} item). Sila kurangkan imej atau tambah token segera.",
        "usage_title": "📊 STATUS DOMPET PREMIUM SAAS",
        "guest_info": "🕒 Dompet Percubaan Tanpa Daftar:\n* Had Harian Digunakan: **{} / 10** Credits (Set semula 24 jam)\n* Penggunaan 30 Hari: **{} / 30** Credits\n* 💡 Jumlah Baki Sedia Ada: **{} item**",
        "welcome": "👋 Selamat kembali: **{}** \n* 🪙 Baki Kredit Freemium: **{} Credits** (Ditolak dahulu)\n* 🪙 Baki Kredit Premium: **{} Credits**\n* 💡 Jumlah Baki Sedia Ada: **{} item**"
    },
    "Bahasa Indonesia": {
        "title": "🌐 AI Sistem Auto-Center Crop & Pengenal Subjek Gambar E-commerce",
        "subtitle": "Pemotongan Otomatis, Pemisahan Objek Massal, dan Konfigurasi Bebas Rasio Ukuran File (Siap)",
        "pricing_html": """
        ### 💰 Pilih Paket Kuasa Produksi Anda (Paket Pengisian Token Credits)
        * **🌟 UJI COBA GRATIS**: **$0** (Daftar langsung dapat **20 Kredit Gratis**!) ── *Uji kehebatan fitur smart centering kami.*
        * **🪙 PAKET PEMULA**: **$4.99** (Dapat **150 Kredit** ── *Hanya sekitar Rp500 per gambar yang sempurna!*)
        * **⚡ PAKET PENJUAL PRO**: **$19.99** (Dapat **700 Kredit** ── *Hanya sekitar Rp430 per gambar yang sempurna!*)
        * **👑 PAKET VAULT RETAIL**: **$49.99** (Dapat **2,000 Kredit** ── **Hemat Ekstrem: Di bawah Rp380 per gambar!**)
        """,
        "param_header": "⚙️ Parameter Rasio & Kapasitas File (Nilai Dapat Disesuaikan)",
        "ratio_lbl": "Rasio kepadatan subjek target (10-99%):",
        "size_lbl": "Batas kapasitas ukuran file maksimum per gambar (MB):",
        "drag_lbl": "📥 SERET GAMBAR TUNGGAL ATAU FOLDER DI SINI (Zona Drop Landasan Raksasa, Gratis Tanpa Registrasi)",
        "loaded_lbl": "📊 Total aset gambar yang dimuat: {} item",
        "clear_btn": "🗑 Bersihkan Antrean",
        "btn_lbl": "🚀 Ekspor Cepat Foto Berpusat Secara Massal Satu-Klik",
        "processing": "⏳ Sistem AI sedang memproses aset gambar {} / {}...",
        "success": "### ✅ Proses AI Selesai! Sebanyak {} aset gambar berhasil dibuat di disk cloud!",
        "dl_btn": "🎁 Buka Kunci & Unduh Paket ZIP",
        "limit_err": "🔒 Blokir Batas Kuota Awal! Jumlah gambar ({} item) melebihi kuota tersedia dompet Anda ({} item). Sila kurangkan jumlah gambar atau top up token sekarang.",
        "usage_title": "📊 STATUS DOMPET PREMIUM ANGGOTA",
        "guest_info": "🕒 Dompet Uji Coba Tanpa Indonesia:\n* Kuota Harian Terpakai: **{} / 10** Credits (Reset 24 jam)\n* Total 30 Hari: **{} / 30** Credits\n* 💡 Sisa Lembar Yang Tersedia: **{} item**",
        "welcome": "👋 Selamat datang kembali: **{}** \n* 🪙 Sisa Kredit Gratis: **{} Credits** (Potong pertama)\n* 🪙 Sisa Kredit Berbayar: **{} Credits**\n* 💡 Sisa Lembar Yang Tersedia: **{} item**"
    }
}

st.set_page_config(page_title="NEXUS CROP — AI SaaS", page_icon="🌐", layout="wide")

# 👑 【免註冊遊客限額雙軌計數狀態機與清除鑰匙初始化】
if "daily_usage" not in st.session_state: st.session_state.daily_usage = 0
if "monthly_usage" not in st.session_state: st.session_state.monthly_usage = 0
if "user_authenticated" not in st.session_state: st.session_state.user_authenticated = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "uploader_key_token" not in st.session_state: st.session_state.uploader_key_token = 1000
    # 👑 👑 👑 【3倍超巨型拖曳方框停機坪 ── CSS 航空級注入晶片】 👑 👑 👑
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

# 🪐 🪐 🪐 【繁簡並排第一順位語言切換選單】 🪐 🪐 🪐
lang = st.selectbox("🌐 Language Interface ｜ 多國語言切換晶片", ("繁體中文", "简体中文", "English", "日本語", "한국어", "ภาษาไทย", "Bahasa Melayu", "Bahasa Indonesia"), index=0)
L = LANG_MAP[lang]

# 👑 👑 👑 【核心動態餘額預先同步解算器】 👑 👑 👑
user_authed = st.session_state.user_authenticated
credits_free = 0
credits_paid = 0
user_uid = ""

if not user_authed:
    rem_daily = max(0, 10 - st.session_state.daily_usage)
    rem_monthly = max(0, 30 - st.session_state.monthly_usage)
    current_remaining_quota = min(rem_daily, rem_monthly)
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

# 👑 全球高級電商雙欄位大氣佈局
main_col, side_col = st.columns([0.72, 0.28], gap="large")

with side_col:
    st.markdown(f"### {L['usage_title']}")
    if not user_authed:
        st.info(L["guest_info"].format(st.session_state.daily_usage, st.session_state.monthly_usage, current_remaining_quota))
        st.markdown("---")
        auth_mode = st.radio("Portal Access", ("Sign In", "Sign Up (Free 20)"), horizontal=True)
        email_in = st.text_input("📧 Email", key="auth_email")
        pass_in = st.text_input("🔒 Password", type="password", key="auth_pass")
        if auth_mode == "Sign Up (Free 20)":
            if st.button("🚀 Establish Account", use_container_width=True):
                try:
                    user = auth.create_user(email=email_in, password=pass_in)
                    if db: db.collection("users").document(user.uid).set({
                        "email": email_in,
                        "credits_free": 20,
                        "credits_paid": 0,
                        "tier": "FREE_TRIAL"
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
        if st.button("🇺🇸 Starter Pack (\$4.99) ── +150 Credits", use_container_width=True, key="side_pack_1"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits_paid": credits_paid + 150})
            st.rerun()
        if st.button("🇺🇸 Power Seller (\$19.99) ── +700 Credits", use_container_width=True, key="side_pack_2"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits_paid": credits_paid + 700})
            st.rerun()
        if st.button("🇺🇸 Mega Vault (\$49.99) ── +2000 Credits", use_container_width=True, type="primary", key="side_pack_3"):
            if db and user_uid: db.collection("users").document(user_uid).update({"credits_paid": credits_paid + 2000})
            st.rerun()
            
        if st.button("🚪 Sign Out Workspace", use_container_width=True):
            st.session_state.user_authenticated = False
            st.session_state.user_email = ""
            st.rerun()

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
    # 👑 👑 👑 【最前端物理安全攔截網】 👑 👑 👑
num_uploaded = len(uploaded_files) if uploaded_files else 0
quota_violation = False

if num_uploaded > 0:
    if num_uploaded > current_remaining_quota:
        quota_violation = True
        st.error(L["limit_err"].format(num_uploaded, current_remaining_quota))

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button(L["clear_btn"], use_container_width=True, key="clear_all_queue"):
        st.session_state.uploader_key_token += 1
        st.session_state.temp_ready = False
        st.rerun()
with col_btn2:
    start_btn = st.button(L["btn_lbl"], type="primary", use_container_width=True, key="start_pipeline", disabled=quota_violation)

# 全域安全路徑對齊防線
zip_path = "/tmp/processed_centered_images.zip"

if uploaded_files and not quota_violation:
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
                    
                    base_name, _ = os.path.splitext(file.name)
                    out_img_name = f"{base_name}_{part_idx}.jpg" if len(valid_boxes) > 1 else f"{base_name}.jpg"
                    with open(os.path.join(temp_out_dir, out_img_name), "wb") as f_out: f_out.write(buf.tobytes())
                    saved += 1
                    
                del img, img_orig, img_rotated, contours_normal, contours_rotated; gc.collect()
            except Exception as e: st.error(f"Error {file.name}: {str(e)}")
            progress_bar.progress(idx / num_uploaded)
        
        if saved > 0:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, _, files in os.walk(temp_out_dir):
                    for f in files: zip_file.write(os.path.join(root, f), f)
            st.session_state.compiled_saved = saved
            st.session_state.temp_ready = True
            st.success(L["success"].format(saved))
            
    if "temp_ready" in st.session_state and st.session_state.temp_ready and os.path.exists(zip_path):
        zip_file_size = os.path.getsize(zip_path)
        if zip_file_size > 0:
            with open(zip_path, "rb") as f_zip:
                zip_data = f_zip.read()
                
            if not user_authed:
                with open(zip_path, "rb") as f_zip:
                    if st.download_button(label=L["dl_btn"], data=zip_data, file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True, key="dl_zip_btn_guest"):
                        st.session_state.daily_usage += num_uploaded
                        st.session_state.monthly_usage += num_uploaded
                        st.session_state.uploader_key_token += 1
                        st.session_state.temp_ready = False
                        st.rerun()
            else:
                with open(zip_path, "rb") as f_zip:
                    if st.download_button(label=L["dl_btn"], data=zip_data, file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True, key="dl_zip_btn_user"):
                        if credits_free >= num_uploaded:
                            new_free = credits_free - num_uploaded
                            new_paid = credits_paid
                        else:
                            remainder = num_uploaded - credits_free
                            new_free = 0
                            new_paid = max(0, credits_paid - remainder)
                            
                        if db and user_uid:
                            db.collection("users").document(user_uid).update({
                                "credits_free": new_free,
                                "credits_paid": new_paid
                            })
                        st.session_state.uploader_key_token += 1
                        st.session_state.temp_ready = False
                        st.rerun()
