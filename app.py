import os, io, zipfile, cv2, gc, shutil, hashlib, numpy as np
from PIL import Image
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from rembg import remove, new_session
from datetime import datetime

# 👑 Firebase 雲端保險箱最高安全初始化連線晶片
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
    return new_session("silueta")

# 👑 實體 IP 雲端探針：直接從網路請求頭中提取實體 IP，封死 F5 漏洞
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
    # 🌍 跨國網拍 SaaS 9 國語言大字典 (第一面：English)
LANG_MAP = {
    "English": {
        "title": "🌐 Smart Subject Recognition & Auto-Center Crop",
        "subtitle": "Trading Card & E-commerce Photo Smart Centering, Batch Splitting, and Weight Control System",
        "pricing_html": """
        ### 💰 Choose Your Production Power (Unified Global Token Wallet)
        * **🌟 FREE TRIAL**: **$0** (Get **50 Free Credits** immediately upon sign up!)
        * **🪙 STARTER PACK**: **$4.99** (Get **150 Credits** - *Tokens never expire, use anytime!*)
        * **⚡ POWER SELLER**: **$19.99** (Get **700 Credits** - *Designed for cross-border high-volume setups.*)
        * **👑 MEGA VAULT**: **$49.99** (Get **2,000 Credits** - **Under $0.025 USD per masterpiece!**)
        """,
        "param_header": "⚙️ Layout Ratio & Capacity Parameters (Customizable Values)",
        "ratio_lbl": "Target subject density ratio (10-99%):",
        "size_lbl": "Maximum payload weight constraint per image (MB):",
        "drag_lbl": "📥 DROP ENTIRE IMAGE FOLDER HERE (Keeps original filenames format)",
        "loaded_lbl": "📊 Consolidated image queue assets: {} items",
        "clear_btn": "🗑 Clear & Reset Queue",
        "btn_lbl": "🚀 One-Click Quick Export Centered Photos",
        "processing": "⏳ Neural pipeline processing asset {} / {}...",
        "success": "### ✅ Pipeline Render Completed! Total {} centered photos compiled! Please click below to download.",
        "dl_btn": "🎁 Download Centering Assets Package (ZIP)",
        "limit_err": "🔒 Sorry, your anonymous trial quota is exhausted. Please sign up to claim 50 free credits bonus instantly, or purchase a token package on the right!",
        "dup_err": "⚠️ Duplicate photos detected! You cannot upload identical images into the dropzone simultaneously. Please reset queue and upload unique photos to avoid duplicate billing.",
        "usage_title": "📊 PREMIUM WORKSPACE WALLET",
        "guest_info": "🕒 Anonymous IP Wallet:\n* Today Used: **{} / 10** Credits (Resets at 00:00 midnight)\n* 30-Day Used: **{} / 30** Credits\n* 💡 Available Balance: **{} items**",
        "welcome": "👋 Welcome, Premium Partner: **{}** \n* 🪙 Total Active Wallet: **{} Credits** (Includes free bonus, lifetime valid)\n* 💡 Available Balance: **{} items**"
    },
     "Deutsch": {
        "title": "🌐 Intelligente Objekterkennung & Auto-Zentrierter Zuschnitt",
        "subtitle": "E-Commerce- und Sammelkarten-Fotos intelligent zentrieren, stapelweise aufteilen und Dateigröße optimieren",
        "pricing_html": """
        ### 💰 Wählen Sie Ihre Produktionsleistung (Einheitliches Guthaben-Konto)
        * **🌟 KOSTENLOSE TESTVERSION**: **$0** (Erhalten Sie sofort **50 Gratis-Credits** bei der Registrierung!)
        * **🪙 STARTER-PAKET**: **$4.99** (Enthält **150 Credits** - *Guthaben läuft nie ab!*)
        * **⚡ POWER-SELLER**: **$19.99** (Enthält **700 Credits** - *Perfekt für hohe Stückzahlen.*)
        * **👑 MEGA-TRESOR**: **$49.99** (Enthält **2.000 Credits** - **Weniger als $0.025 pro perfektem Foto!**)
        """,
        "param_header": "⚙️ Parameter für Layout-Verhältnis & Dateigröße",
        "ratio_lbl": "Ziel-Dichte des Hauptobjekts (10-99%):",
        "size_lbl": "Maximale Dateigrößenbeschränkung pro Bild (MB):",
        "drag_lbl": "📥 ZIEHEN SIE DEN GESAMTEN BILDERORDNER HIERHER (Behält das ursprüngliche Dateinamenformat bei)",
        "loaded_lbl": "📊 Geladene Medien-Assets: {} Elemente",
        "clear_btn": "🗑 Warteschlange zurücksetzen",
        "btn_lbl": "🚀 Zentrierte Fotos mit einem Klick exportieren",
        "processing": "⏳ Verarbeitung läuft: Bild {} / {}...",
        "success": "### ✅ Verarbeitung abgeschlossen! Insgesamt {} zentrierte Fotos erstellt! Bitte unten herunterladen.",
        "dl_btn": "🎁 Zentrierte Bilder herunterladen (ZIP)",
        "limit_err": "🔒 Entschuldigung, Ihr anonymes Testguthaben ist aufgebraucht. Bitte registrieren Sie sich rechts, um 50 Gratis-Credits zu erhalten, oder kaufen Sie ein Paket!",
        "dup_err": "⚠️ Doppelte Fotos erkannt! Sie können identische Bilder nicht gleichzeitig hochladen. Bitte Warteschlange zurücksetzen.",
        "usage_title": "📊 PREMIUM WORKSPACE WALLET",
        "guest_info": "🕒 Anonymes IP-Guthaben:\n* Heute genutzt: **{} / 10** Credits (Zurücksetzung um Mitternacht)\n* 30-Tage genutzt: **{} / 30** Credits\n* 💡 Verfügbares Guthaben: **{} Bilder**",
        "welcome": "👋 Willkommen, Premium-Partner: **{}** \n* 🪙 Gesamtguthaben: **{} Credits** (Lebenslang gültig)\n* 💡 Verfügbares Guthaben: **{} Bilder**"
    },
    "Français": {
        "title": "🌐 Reconnaissance Inteligente de l'Objet & Recadrage Centré",
        "subtitle": "Centrage intelligent, division par lots et contrôle du poids des photos e-commerce et cartes à collectionner",
        "pricing_html": """
        ### 💰 Choisissez Votre Puissance de Production (Portefeuille de Crédits Unique)
        * **🌟 ESSAI GRATUIT**: **$0** (Obtenez **50 crédits gratuits** dès votre inscription !)
        * **🪙 PACK SOUVENT**: **$4.99** (Comprend **150 crédits** - *Les crédits n'expirent jamais !*)
        * **⚡ VENDEUR PRO**: **$19.99** (Comprend **700 crédits** - *Idéal pour les gros volumes de production.*)
        * **👑 MEGA COFFRE**: **$49.99** (Comprend **2 000 crédits** - **Moins de 0,025 $ par photo parfaite !**)
        """,
        "param_header": "⚙️ Paramètres de Proportion du Mises en Page & Poids de Fichier",
        "ratio_lbl": "Ratio de densité de l'objet cible (10-99%) :",
        "size_lbl": "Limite de poids maximale par image (Mo) :",
        "drag_lbl": "📥 GLISSEZ LE DOSSIER D'IMAGES ICI (Conserve le format des noms de fichiers originaux)",
        "loaded_lbl": "📊 Actifs multimédias chargés : {} éléments",
        "clear_btn": "🗑 Réinitialiser la file d'attente",
        "btn_lbl": "🚀 Exporter les photos centrées en un clic",
        "processing": "⏳ Traitement en cours : Image {} / {}...",
        "success": "### ✅ Traitement terminé ! {} photos centrées générées au total ! Veuillez cliquer ci-dessous pour télécharger.",
        "dl_btn": "🎁 Télécharger le package d'images centrées (ZIP)",
        "limit_err": "🔒 Désolé, votre quota d'essai anonyme est épuisé. Veuillez vous inscrire à droite pour réclamer 50 crédits gratuits, ou achetez un pack !",
        "dup_err": "⚠️ Photos en double détectées ! Vous ne pouvez pas télécharger des images identiques simultanément. Veuillez réinitialiser la file d'attente.",
        "usage_title": "📊 PREMIUM WORKSPACE WALLET",
        "guest_info": "🕒 Portefeuille IP Anonyme :\n* Utilisé aujourd'hui : **{} / 10** crédits (Réinitialisé à minuit)\n* Utilisé sur 30 jours : **{} / 30** crédits\n* 💡 Solde disponible : **{} éléments**",
        "welcome": "👋 Bienvenue, Partenaire Premium : **{}** \n* 🪙 Solde total actif : **{} crédits** (Valable à vie)\n* 💡 Solde disponible : **{} éléments**"
    },
    "繁體中文": {
        "title": "🌐 網拍電商商品照片 ── 智慧自動置中裁剪系統",
        "subtitle": "卡牌、網拍商品照一鍵自動裁切、主體完美置中、圖檔比例容量自由設定",
        "pricing_html": """
        ### 💰 選擇您的智慧生產力方案 (隨買隨用 合併大錢包點數包)
        * **🌟 免費體驗**: **$0** (註冊登入即送 **50 免費點數**！) ── *體驗強大原圖裁切防線。*
        * **🪙 賣家入門包**: **$4.99** (內含 **150 點數** ── *點數永久有效，不限時間數量！*)
        * **⚡ 大賣家衝刺包**: **$19.99** (內含 **700 點數** ── *跨境大賣家高生產力黃金套餐！*)
        * **👑 跨境卡牌大亨包**: **$49.99** (內含 **2,000 點數** ── **極致極限：每張照片不到 0.8 元台幣！**)
        """,
        "param_header": "⚙️ 圖檔比例容量參數 (可自訂數值)",
        "ratio_lbl": "導出後主體佔畫面比例 (10-99%):",
        "size_lbl": "導出後照片檔最大容量限制 (MB):",
        "drag_lbl": "📥 將「單張相片」或「整個圖片資料夾」全數拖曳至此（原檔名導出流，免註冊免費體驗）",
        "loaded_lbl": "📊 目前已載入商品照片：{} 張",
        "clear_btn": "🗑 清除重選",
        "btn_lbl": "🚀 一鍵快速導出完美置中商品照片",
        "processing": "⏳ 智慧光學解算中：第 {} 張 / 共 {} 張...",
        "success": "### ✅ 核心解算成功！共生成 {} 張智慧置中照片！請點選下方按鈕下載打包！",
        "dl_btn": "🎁 點擊下載完美置中相片壓縮包 (ZIP)",
        "limit_err": "🔒 抱歉，您的免註冊試用額度已用完。歡迎在右側註冊登入直接領取免費 50 點大禮包，或立即充值點數套餐包解鎖更高生產力！",
        "dup_err": "⚠️ 偵測到重複上傳相同照片！框框內不可重複置入相同圖檔（即使更換檔名亦會被安全攔截），請使用清除重選並重新拉入純淨不重複的照片，以防止點數重複扣除爭議！",
        "usage_title": "📊 NEXUS CROP 會員錢包看板",
        "guest_info": "🕒 免註冊 IP 試用錢包：\n* 今日已用額度：**{} / 10** Credits (午夜12點全自動清空歸零)\n* 30日累計使用：**{} / 30** Credits (雲端 IP 實體追蹤)\n* 💡 剩餘可用總張數：**{} 張**",
        "welcome": "👋 歡迎回來，尊貴的電商夥伴：**{}** \n* 🪙 專屬錢包總餘額：**{} Credits** (含免費贈點，永久無時間數量限制)\n* 💡 剩餘可導出總張數：**{} 張**"
    },
    "简体中文": {
        "title": "🌐 网拍电商商品照片 ── 智慧自动置中裁剪系统",
        "subtitle": "卡牌、网拍商品照一键自动裁切、主体完美置中、图档比例容量自由设定",
        "pricing_html": """
        ### 💰 选择您的智慧生产力方案 (随买随用 统一合并钱包点数包)
        * **🌟 免费体验**: **$0** (注册登录即送 **50 免费点数**！) ── *体验强大原图裁切防线。*
        * **🪙 卖家入门包**: **$4.99** (内含 **150 点数** ── *点数永久有效，不限时间数量！*)
        * **⚡ 大卖家冲刺包**: **$19.99** (内含 **700 点数** ── *跨境大卖家高生产力黄金套餐！*)
        * **👑 跨境卡牌大亨包**: **$49.99** (内含 **2,000 点数** ── **极致极限：每张照片不到 0.17 元人民币！**)
        """,
        "param_header": "⚙️ 图档比例容量参数 (可自订数值)",
        "ratio_lbl": "导出后主体占画面比例 (10-99%):",
        "size_lbl": "导出后照片档 maximum 容量限制 (MB):",
        "drag_lbl": "📥 将单张相片 or 整个图片文件夹全数拖拽至此（原档名导出流，免注册免费体验）",
        "loaded_lbl": "📊 目前已载入商品照片：{} 张",
        "clear_btn": "🗑 清除重选",
        "btn_lbl": "🚀 一键快速导出完美置中商品照片",
        "processing": "⏳ 智慧光学解算中：第 {} 张 / 共 {} 张...",
        "success": "### ✅ 核心解算成功！共生成 {} 张智慧置中照片！请点击下方按钮下载打包！",
        "dl_btn": "🎁 点击下载完美置中相片压缩包 (ZIP)",
        "limit_err": "🔒 抱歉，您的免注册试用额度已用完。欢迎在右侧注册登录直接领取免费 50 点大礼包，or 立即充值点数套餐包解锁更高生产力！",
        "dup_err": "⚠️ 侦测到重复上传相同照片！框框内不可重复置入相同图档（即使更换档名亦会被安全拦截），请使用清除重选并重新拉入纯净不重复的照片，以防止点数重复扣除争议！",
        "usage_title": "📊 NEXUS CROP 会员钱包看板",
        "guest_info": "🕒 免注册 IP 试用钱包：\n* 今日已用额度：**{} / 10** Credits (午夜12点全自动清空归零)\n* 30日累计使用：**{} / 30** Credits\n* 💡 剩余可用总张数：**{} 张**",
        "welcome": "👋 欢迎回来，尊贵的电商伙伴：**{}** \n* 🪙 专属钱包总余额：**{} Credits** (含免费赠点，永久无时间数量限制)\n* 💡 剩余可导出总张数：**{} 张**"
    },
    "日本語": {
        "title": "🌐 AI 商品画像自動中央配置＆自動クロップシステム",
        "subtitle": "トレカ・EC商品画像の自動クロップ・複数分割・容量と比率の自由設定",
        "pricing_html": """
        ### 💰 プランを選択してください (随時利用可能な 合併大ウォレットパック)
        * **🌟 無料体験**: **$0** (新規登録・ログインで **50 無料トークン** プレゼント！)
        * **🪙 スターターパック**: **$4.99** ( **150 トークン** ── *トークンは永久に有効、時間や枚数の制限なし！*)
        * **⚡ パワーセラーパック**: **$19.99** ( **700 トークン** ── *クロスボーダー大口セラー向けゴールデンセット！*)
        * **👑 メガバルトパック**: **$49.99** ( **2,000 トークン** 内蔵 ── **圧倒的コスパ！**)
        """,
        "param_header": "⚙️ 画像比率とファイル容量パラメータ (カスタム数値可能)",
        "ratio_lbl": "出力後の商品主体の表示比率 (10-99%):",
        "size_lbl": "出力画像の最大容量制限 (MB):",
        "drag_lbl": "📥 画像フォルダをここにドラッグ＆ドロップ (元のファイル名を維持)",
        "loaded_lbl": "📊 読み込まれた画像：{} 枚",
        "clear_btn": "🗑 キューをクリア",
        "btn_lbl": "🚀 ワンクリックで中央配置画像を高速エクスポート",
        "processing": "⏳ 解析中：第 {} 枚 / 全 {} 枚...",
        "success": "### ✅ 解析完了！トークンは正常に消費されました。合計 {} 枚の画像が生成されました！",
        "dl_btn": "🎁 クロップ画像をダウンロード (ZIP)",
        "limit_err": "🔒 申し訳ありませんが、無料お試し枠は終了しました。右側で無料登録して50点大礼箱を受け取るか、パッケージを購入してください！",
        "dup_err": "⚠️ 重複画像が検出されました！同じ写真を複数アップロードすることはできません。重複請求を防ぐため、ファイルを整理して再試行してください。",
        "usage_title": "📊 プレミアム会員ウォレット状況",
        "guest_info": "🕒 IPお試し財布:\n* 本日の使用量: **{} / 10** Credits (夜12時に全自動リセット)\n* 30日間の使用量: **{} / 30** Credits\n* 💡 残り利用可能枚数: **{} 枚**",
        "welcome": "👋 お帰りなさい: **{}** \n* 🪙 統合ウォレット残高: **{} Credits** (生涯有効)\n* 💡 残り利用可能枚数: **{} 枚**"
    },
    "한국어": {
        "title": "🌐 AI 이커머스 상품 이미지 자동 중앙 배치 시스템",
        "subtitle": "트레이딩 카드 및 쇼핑몰 상품 이미지 크롭, 다중 분할 및 비율 용량 자유 설정",
        "pricing_html": """
        ### 💰 요금제 선택 (충전식 통합 대형 지갑 팩)
        * **🌟 무료 체험**: **$0** (가입 시 **50 무료 토큰** 즉시 지급!)
        * **🪙 스타터 팩**: **$4.99** ( **150 토큰** 포함 ── *토큰은 만료일 없이 평생 사용 가능!*)
        * **⚡ 파워 셀러 팩**: **$19.99** ( **700 토큰** 포함 ── *글로벌 대형 셀러를 위한 강력 추천 패키지!*)
        * **👑 메가 볼트 팩**: **$49.99** ( **2,000 토큰** 포함 ── **최고의 가성비 토큰 패키지!**)
        """,
        "param_header": "⚙️ 배치 비율 및 파일 용량 매개변수 (값 자율 지정 가능)",
        "ratio_lbl": "출력 후 객체 화면 비율 (10-99%):",
        "size_lbl": "출력 이미지 최대 용량 제한 (MB):",
        "drag_lbl": "📥 이미지 폴더를 여기에 드래그 앤 드롭 (원본 파일 이름 유지)",
        "loaded_lbl": "📊 로드된 상품 이미지: {} 장",
        "clear_btn": "🗑 대기열 비우기",
        "btn_lbl": "🚀 원클릭 일괄 중앙 배치 이미지 신속 내보내기",
        "processing": "⏳ 분석 중: {} / {} 번째 이미지 처리 중...",
        "success": "### ✅ 분석 완료! 토큰이 성공적으로 차감되었습니다. 총 {} 장의 이미지가 생성되었습니다!",
        "dl_btn": "🎁 압축 패키지 다운로드 (ZIP)",
        "limit_err": "🔒 죄송합니다, 무료 체험 한도가 초과되었습니다. 오른쪽에서 무료 가입하고 50 토큰 대형 보너스를 받거나 패키지를 충전하세요!",
        "dup_err": "⚠️ 중복 파일이 감지되었습니다! 동일한 사진을 중복으로 올릴 수 없습니다. 대기열을 비우고 다시 시도해주세요.",
        "usage_title": "📊 프리미엄 회원 지갑 상태",
        "guest_info": "🕒 IP 체험 지갑:\n* 금일 사용량: **{} / 10** Credits (자정에 자동 초기화)\n* 30일 사용량: **{} / 30** Credits\n* 💡 남은 이용 가능 장수: **{} 장**",
        "welcome": "👋 어서 오세요, 프리미엄 파트너: **{}** \n* 🪙 통합 지갑 총잔액: **{} Credits** (평생 유효)\n* 💡 남은 이용 가능 장수: **{} 장**"
    },
    "Bahasa Melayu": {
        "title": "🌐 AI Sistem Centering & Pemotongan Gambar E-dagang",
        "subtitle": "Pemotongan Automatik, Pengasingan Gambar Pukal, dan Tetapan Bebas Saiz Fail Sasaran",
        "pricing_html": """
        ### 💰 Pilih Pakej Kuasa Pengeluaran Anda (Dompet Token Bersepadu)
        * **🌟 PERCUBAAN PERCUMA**: **$0** (Daftar masuk dapat **50 Kredit Percuma** segera!)
        * **🪙 PAKEJ PERMULAAN**: **$4.99** (Dapat **150 Kredit** ── *Token sah selama-lamanya!*)
        * **⚡ PAKEJ PENJUAL AKTIF**: **$19.99** (Dapat **700 Kredit** ── *Pelan terbaik untuk penjual antarabangsa.*)
        * **👑 PAKEJ GERGASI SAAS**: **$49.99** (Dapat **2,000 Kredit** ── **Nilai hebat di bawah $0.025 setiap gambar!**)
        """,
        "param_header": "⚙️ Parameter Nisbah & Kapasiti Fail (Nilai Boleh Diubahsuai)",
        "ratio_lbl": "Nisbah kepadatan subjek sasaran (10-99%):",
        "size_lbl": "Had saiz fail maksimum per imej (MB):",
        "drag_lbl": "📥 Seret folder gambar ke sini (Kekalkan nama format fail asal)",
        "loaded_lbl": "📊 Aset imej terkumpul: {} item",
        "clear_btn": "🗑 Padam & Set Semula",
        "btn_lbl": "🚀 Eksport Gambar Centered Secara Pukal Satu-Klik",
        "processing": "⏳ Saluran paip neural memproses aset {} / {}...",
        "success": "### ✅ Proses Selesai! Kredit telah ditolak. Sebanyak {} aset telah dijana!",
        "dl_btn": "🎁 Muat Turun Pakej ZIP Gambar",
        "limit_err": "🔒 Maaf, kuota trial tanpa pendaftaran anda telah habis. Sila daftar akaun percuma untuk tebus bonus 50 kredit segera atau beli pakej token di sebelah kanan!",
        "dup_err": "⚠️ Gambar bertindih dikesan! Anda tidak boleh memuat naik imej yang sama. Sila kosongkan barisan untuk mengelakkan pemotongan kredit ganda.",
        "usage_title": "📊 STATUS DOMPET PREMIUM SAAS",
        "guest_info": "🕒 Dompet IP Anonim:\n* Digunakan Hari Ini: **{} / 10** Credits (Set semula pada tengah malam)\n* Had 30 Hari Digunakan: **{} / 30** Credits\n* 💡 Jumlah Baki Sedia Ada: **{} item**",
        "welcome": "👋 Selamat kembali: **{}** \n* 🪙 Baki Dompet Bersepadu: **{} Credits** (Sah seumur hidup)\n* 💡 Jumlah Baki Sedia Ada: **{} item**"
    },
    "Bahasa Indonesia": {
        "title": "🌐 AI Sistem Auto-Center Crop & Pengenal Subjek Gambar E-commerce",
        "subtitle": "Pemotongan Otomatis, Pemisahan Objek Massal, dan Konfigurasi Bebas Rasio Ukuran File",
        "pricing_html": """
        ### 💰 Pilih Paket Kuasa Produksi Anda (Dompet Terpadu Massal)
        * **🌟 UJI COBA GRATIS**: **$0** (Daftar akun langsung dapat **50 Kredit Gratis** !)
        * **🪙 Paket PEMULA**: **$4.99** (Dapat **150 Kredit** ── *Token berlaku selamanya, tanpa kedaluwarsa!*)
        * **⚡ PAKET PENJUAL PRO**: **$19.99** (Dapat **700 Kredit** ── *Sangat direkomendasikan untuk penjual lintas batas.*)
        * **👑 Paket VAULT RETAIL**: **$49.99** (Dapat **2,000 Kredit** ── **Sangat hemat di bawah $0.025 per gambar!**)
        """,
        "param_header": "⚙️ Parameter Rasio & Kapasitas File (Nilai Dapat Disesuaikan)",
        "ratio_lbl": "Rasio kepadatan subjek target (10-99%):",
        "size_lbl": "Batas kapasitas ukuran file maksimum per gambar (MB):",
        "drag_lbl": "📥 Seret folder gambar ke sini (Pertahankan format nama file asli)",
        "loaded_lbl": "📊 Total aset gambar yang dimuat: {} item",
        "clear_btn": "🗑 Bersihkan Antrean",
        "btn_lbl": "🚀 Ekspor Cepat Foto Berpusat Secara Massal Satu-Klik",
        "processing": "⏳ Sistem AI sedang memproses aset gambar {} / {}...",
        "success": "### ✅ Bayes AI Selesai! Kredit berhasil dipotong, sebanyak {} aset gambar dibuat!",
        "dl_btn": "🎁 Unduh Paket ZIP Gambar Berpusat",
        "limit_err": "🔒 Maaf, batas uji coba tanpa pendaftaran Anda sudah habis. Silakan mendaftar gratis di sebelah kanan untuk mengklaim bonus 50 kredit, atau beli paket token!",
        "dup_err": "⚠️ Duplikasi foto terdeteksi! Anda tidak dapat mengunggah gambar yang sama persis secara bersamaan. Silakan bersihkan antrean.",
        "usage_title": "📊 STATUS DOMPET PREMIUM ANGGOTA",
        "guest_info": "🕒 Dompet IP Anonim:\n* Kuota Terpakai Hari Ini: **{} / 10** Credits (Reset otomatis jam 12 malam)\n* Kuota 30 Hari Terpakai: **{} / 30** Credits\n* 💡 Sisa Lembar Yang Tersedia: **{} item**",
        "welcome": "👋 Selamat datang kembali: **{}** \n* 🪙 Saldo Dompet Terpadu: **{} Credits** (Berlaku seumur hidup)\n* 💡 Sisa Lembar Yang Tersedia: **{} item**"
    }
}

# 👑 裝載指定最高排序母語清單
lang = st.selectbox("🌐 Language Interface ｜ 多國語言切換晶片", ("English", "Deutsch", "Français", "繁體中文", "简体中文", "日本語", "한국어", "Bahasa Melayu", "Bahasa Indonesia"), index=3)
L = LANG_MAP[lang]
# 👑 👑 👑 【實體 IP 雲端資料庫雙軌追蹤大腦】 👑 👑 👑
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
            else:
                guest_used_day = 0
            if ip_data.get("last_month") == current_month_str:
                guest_used_month = ip_data.get("month_used", 0)
            else:
                guest_used_month = 0
    except:
        pass

# 👑 雙軌計數加總解算
if not user_authed:
    rem_day = max(0, 10 - guest_used_day)
    rem_month = max(0, 30 - guest_used_month)
    current_remaining_quota = min(rem_day, rem_month)
else:
    if db:
        try:
            user_rec = auth.get_user_by_email(st.session_state.user_email)
            user_uid = user_rec.uid
            user_doc_ref = db.collection("users").document(user_uid)
            user_data = user_doc_ref.get().to_dict()
            credits_total = user_data.get("credits_total", 0)
        except:
            credits_total = 50
    current_remaining_quota = credits_total

# 高級電商雙欄布局
main_col, side_col = st.columns([0.72, 0.28], gap="large")

with side_col:
    st.markdown(f"### {L['usage_title']}")
    if not user_authed:
        st.info(L["guest_info"].format(guest_used_day, guest_used_month, current_remaining_quota))
        st.markdown("---")
        auth_mode = st.radio("Portal Access", ("Sign In", "Sign Up (Free 50)"), horizontal=True)
        email_in = st.text_input("📧 Email", key="auth_email")
        pass_in = st.text_input("🔒 Password", type="password", key="auth_pass")
        if auth_mode == "Sign Up (Free 50)":
            if st.button("🚀 Establish Account", use_container_width=True):
                try:
                    user = auth.create_user(email=email_in, password=pass_in)
                    if db: db.collection("users").document(user.uid).set({
                        "email": email_in, "credits_total": 50, "tier": "PREMIUM_WORKSPACE"
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
        st.success(L["welcome"].format(st.session_state.user_email, credits_total, current_remaining_quota))
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

# 🪐 拼接臨界點：此處開啟 with 閘門，下方第九與第十部分全部精密往右縮排 4 個空格！
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

    num_uploaded = len(uploaded_files) if uploaded_files else 0
    quota_violation = False
    duplicate_violation = False

    if num_uploaded > 0:
        if num_uploaded > current_remaining_quota:
            quota_violation = True
            st.error(L["limit_err"])
        
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
                    file_raw_name = getattr(file, "name", "photo.jpg")
                    file.seek(0)
                    file_bytes = np.frombuffer(file.read(), dtype=np.uint8)
                    img_orig = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                    if img_orig is None: continue
                    
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
                    
                    if valid_cnt_rotated > valid_cnt_normal:
                        img = img_rotated; contours = contours_rotated; is_rotated_for_calculation = True; h, w = h_r, w_r
                    else:
                        img = img_orig; contours = contours_normal; is_rotated_for_calculation = False; h, w = h_o, w_o
                    
                    valid_boxes = []
                    # 👑 100% 完美回歸您補貼的後半段二次去背、大框替換子邊界過濾內核流！
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
                    
                    # 👑 100% 完美回歸純原圖最大化物理邊界卡位演算法
                    for part_idx, (bx, by, bw, bh) in enumerate(valid_boxes, 1):
                        cx, cy = bx + bw // 2, by + bh // 2
                        ideal_pad_w = int((bw / ratio - bw) / 2)
                        ideal_pad_h = int((bh / ratio - bh) / 2)
                        
                        pad_l = min(cx - bw // 2, ideal_pad_w)
                        pad_r = min((w - cx) - bw // 2, ideal_pad_w)
                        pad_t = min(cy - bh // 2, ideal_pad_h)
                        pad_b = min((h - cy) - bh // 2, ideal_pad_h)
                        
                        x1 = cx - bw // 2 - pad_l
                        x2 = cx + bw // 2 + pad_r
                        y1 = cy - bh // 2 - pad_t
                        y2 = cy + bh // 2 + pad_b
                        
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
                            out_img_name = f"{base_name}_裁切_{part_idx}.jpg"
                        else:
                            out_img_name = f"{base_name}.jpg"
                        with open(os.path.join(temp_out_dir, out_img_name), "wb") as f_out: f_out.write(buf.tobytes())
                        saved += 1
                        
                    del img, img_orig, img_rotated, contours_normal, contours_rotated; gc.collect()
                except Exception as e: st.error(f"Error {file_raw_name}: {str(e)}")
                progress_bar.progress(idx / num_uploaded)
            
            if saved > 0:
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for root, _, files in os.walk(temp_out_dir):
                        for f in files: zip_file.write(os.path.join(root, f), f)
                st.session_state.compiled_saved = saved
                st.session_state.temp_ready = True
                st.success(L["success"].format(num_uploaded))
                st.rerun()
                
        # 🔓 🔓 🔓 【下載點擊一瞬間才雲端扣點流】 🔓 🔓 🔓
        if "temp_ready" in st.session_state and st.session_state.temp_ready and os.path.exists(zip_path):
            zip_file_size = os.path.getsize(zip_path)
            if zip_file_size > 0:
                with open(zip_path, "rb") as f_zip:
                    zip_data = f_zip.read()
                
                if st.download_button(label=L["dl_btn"], data=zip_data, file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True, key="dl_zip_btn_final_gate"):
                    if not user_authed:
                        if db and visitor_ip != "127.0.0.1":
                            new_day = guest_used_day + num_uploaded
                            new_month = guest_used_month + num_uploaded
                            db.collection("guest_ips").document(visitor_ip).set({
                                "day_used": new_day, "month_used": new_month,
                                "last_date": current_date_str, "last_month": current_month_str
                            })
                    else:
                        new_total = max(0, credits_total - num_uploaded)
                        if db and user_uid: db.collection("users").document(user_uid).update({"credits_total": new_total})
                    st.session_state.uploader_key_token += 1
                    st.session_state.temp_ready = False
                    st.rerun()
