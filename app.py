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

# 👑 雲端快取優化：確保 AI 去背模型在雲端唯一下載一次，節省效能開銷
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
# 👑 100% 遵照創辦人最高指示：剔除所有欺騙性的去背字眼，換上最硬核專業的裁切縮放誠實文案！
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
        "param_header": "⚙️ 電商智慧識別參數設定 (支援鍵盤手動自行打字輸入數值)",
        "ratio_lbl": "導出後主體佔畫面比例 (10-99%):",
        "size_lbl": "導出後照片檔最大容量限制 (MB):",
        "drag_lbl": "📥 將「單張相片」或「整個圖片資料夾」全數拖曳至此（超巨型拖曳停機坪，免註冊免費體驗，25張大文件通殺）",
        "loaded_lbl": "📊 目前已載入商品照片：{} 張",
        "clear_btn": "🗑 清除重選",
        "btn_lbl": "🚀 一鍵快速導出完美置中商品照片",
        "processing": "⏳ 智慧光學解算中：第 {} 張 / 共 {} 張...",
        "success": "### ✅ 核心解算成功！共生成 {} 張智慧置中照片！",
        "dl_btn": "🎁 點擊解鎖並下載完美置中相片壓縮包 (ZIP)",
        "limit_err": "🔒 相片打包已安全鎖死 ── 免註冊試用額度（每天限 10 Credits）已用完！請在右側註冊登入，或充值點數套餐，即可立刻全速下載您改好的高畫質 ZIP 壓縮檔！",
        "usage_title": "📊 NEXUS CROP 會員錢包看板",
        "guest_info": "🕒 免註冊試用錢包：\n* 當日已用點數：**{} / 10** Credits\n*(每24小時全自動重置歸零)*",
        "welcome": "👋 歡迎回來，尊貴的電商夥伴：**{}** ｜ 🪙 專屬錢包餘額：**{} Credits**"
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
        "param_header": "⚙️ 电商智慧识别参数设置 (支持键盘手动自行打字输入数值)",
        "ratio_lbl": "导出后主体占画面比例 (10-99%):",
        "size_lbl": "导出后照片档最大容量限制 (MB):",
        "drag_lbl": "📥 将单张相片 or 整个图片文件夹全数拖拽至此（超巨型拖拽停机坪，免注册免费体验，25张大文件通杀）",
        "loaded_lbl": "📊 目前已载入商品照片：{} 张",
        "clear_btn": "🗑 清除重选",
        "btn_lbl": "🚀 一键快速导出完美置中商品照片",
        "processing": "⏳ 智慧光学解算中：第 {} 张 / 共 {} 张...",
        "success": "### ✅ 核心解算成功！共生成 {} 张智慧置中照片！",
        "dl_btn": "🎁 点击解锁并下载完美置中相片压缩包 (ZIP)",
        "limit_err": "🔒 相片打包已安全锁死 ── 免注册试用额度（每天限 10 Credits）已用完！请在右侧注册登录，or 充值点数套餐，即可立刻全速下载您改好的高画质 ZIP 压缩档！",
        "usage_title": "📊 NEXUS CROP 会员钱包看板",
        "guest_info": "🕒 免注册试用钱包：\n* 当日已用点数：**{} / 10** Credits\n*(每24小时全自动重置归零)*",
        "welcome": "👋 欢迎回来，尊贵的电商伙伴：**{}** ｜ 🪙 专属钱包余额：**{} Credits**"
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
        "param_header": "⚙️ AI Optimization & Parameter Infrastructure (Keyboard input enabled)",
        "ratio_lbl": "Target subject density ratio (10-99%):",
        "size_lbl": "Maximum payload weight constraint per image (MB):",
        "drag_lbl": "📥 DROP SINGLE IMAGES OR ENTIRE IMAGE FOLDER HERE FOR FREE NEURAL CENTERING",
        "loaded_lbl": "📊 Consolidated image queue assets: {} items",
        "clear_btn": "🗑 Clear & Reset Queue",
        "btn_lbl": "🚀 One-Click Quick Export Centered Photos",
        "processing": "⏳ Neural pipeline processing asset {} / {}...",
        "success": "### ✅ Pipeline Render Completed! Total {} assets compiled in cloud disk!",
        "dl_btn": "🎁 Unlock & Download Centering Assets Package (ZIP)",
        "limit_err": "🔒 DEPLOYMENT PACK LOCKED ── Free trial quota cap exceeded (Max 10 Credits/24H). Please sign in or purchase token packages below to unlock high-res ZIP package immediately.",
        "usage_title": "📊 PREMIUM WORKSPACE WALLET",
        "guest_info": "🕒 Unregistered Free Tier:\n* Daily Used: **{} / 10** Credits\n*(Resets every 24 hours)*",
        "welcome": "👋 Welcome, Premium Partner: **{}** ｜ 🪙 Wallet Balance: **{} Credits**"
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
        "param_header": "⚙️ AI最適化パラメータ設定 (キーボード手動入力対応)",
        "ratio_lbl": "出力後の商品主体の表示比率 (10-99%):",
        "size_lbl": "出力画像の最大容量制限 (MB):",
        "drag_lbl": "📥 画像またはフォルダをここにドラッグ＆ドロップ (超巨大ドロップゾーン、無料トライアル対応)",
        "loaded_lbl": "📊 読み込まれた画像：{} 枚",
        "clear_btn": "🗑 キューをクリア",
        "btn_lbl": "🚀 ワンクリックで中央配置画像を高速エクスポート",
        "processing": "⏳ 解析中：第 {} 枚 / 全 {} 枚...",
        "success": "### ✅ 解析完了！合計 {} 枚 of 画像がクラウドで生成されました！",
        "dl_btn": "🎁 パッケージを解鎖してダウンロード (ZIP)",
        "limit_err": "🔒 パッケージがロックされました ── 無料枠制限(1日10 Creditsまで)を超えました。右側でログインするか、トークンを購入してダウンロードしてください。",
        "usage_title": "📊 プレミアム会員ウォレット状況",
        "guest_info": "🕒 未登録の無料プラン:\n* 本日の使用量: **{} / 10** Credits\n*(24時間ごとに自動リセット)*",
        "welcome": "👋 お帰りなさい、プレミアムパートナー: **{}** ｜ 🪙 残りトークン: **{} Credits**"
    },
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

# 👑 雲端快取優化：確保 AI 去背模型在雲端唯一下載一次，節省效能開銷
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
# 👑 100% 遵照創辦人最高指示：剔除所有欺騙性的去背字眼，換上最硬核專業的裁切縮放誠實文案！
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
        "param_header": "⚙️ 電商智慧識別參數設定 (支援鍵盤手動自行打字輸入數值)",
        "ratio_lbl": "導出後主體佔畫面比例 (10-99%):",
        "size_lbl": "導出後照片檔最大容量限制 (MB):",
        "drag_lbl": "📥 將「單張相片」或「整個圖片資料夾」全數拖曳至此（超巨型拖曳停機坪，免註冊免費體驗，25張大文件通殺）",
        "loaded_lbl": "📊 目前已載入商品照片：{} 張",
        "clear_btn": "🗑 清除重選",
        "btn_lbl": "🚀 一鍵快速導出完美置中商品照片",
        "processing": "⏳ 智慧光學解算中：第 {} 張 / 共 {} 張...",
        "success": "### ✅ 核心解算成功！共生成 {} 張智慧置中照片！",
        "dl_btn": "🎁 點擊解鎖並下載完美置中相片壓縮包 (ZIP)",
        "limit_err": "🔒 相片打包已安全鎖死 ── 免註冊試用額度（每天限 10 Credits）已用完！請在右側註冊登入，或充值點數套餐，即可立刻全速下載您改好的高畫質 ZIP 壓縮檔！",
        "usage_title": "📊 NEXUS CROP 會員錢包看板",
        "guest_info": "🕒 免註冊試用錢包：\n* 當日已用點數：**{} / 10** Credits\n*(每24小時全自動重置歸零)*",
        "welcome": "👋 歡迎回來，尊貴的電商夥伴：**{}** ｜ 🪙 專屬錢包餘額：**{} Credits**"
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
        "param_header": "⚙️ 电商智慧识别参数设置 (支持键盘手动自行打字输入数值)",
        "ratio_lbl": "导出后主体占画面比例 (10-99%):",
        "size_lbl": "导出后照片档最大容量限制 (MB):",
        "drag_lbl": "📥 将单张相片 or 整个图片文件夹全数拖拽至此（超巨型拖拽停机坪，免注册免费体验，25张大文件通杀）",
        "loaded_lbl": "📊 目前已载入商品照片：{} 张",
        "clear_btn": "🗑 清除重选",
        "btn_lbl": "🚀 一键快速导出完美置中商品照片",
        "processing": "⏳ 智慧光学解算中：第 {} 张 / 共 {} 张...",
        "success": "### ✅ 核心解算成功！共生成 {} 张智慧置中照片！",
        "dl_btn": "🎁 点击解锁并下载完美置中相片压缩包 (ZIP)",
        "limit_err": "🔒 相片打包已安全锁死 ── 免注册试用额度（每天限 10 Credits）已用完！请在右侧注册登录，or 充值点数套餐，即可立刻全速下载您改好的高画质 ZIP 压缩档！",
        "usage_title": "📊 NEXUS CROP 会员钱包看板",
        "guest_info": "🕒 免注册试用钱包：\n* 当日已用点数：**{} / 10** Credits\n*(每24小时全自动重置归零)*",
        "welcome": "👋 欢迎回来，尊贵的电商伙伴：**{}** ｜ 🪙 专属钱包余额：**{} Credits**"
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
        "param_header": "⚙️ AI Optimization & Parameter Infrastructure (Keyboard input enabled)",
        "ratio_lbl": "Target subject density ratio (10-99%):",
        "size_lbl": "Maximum payload weight constraint per image (MB):",
        "drag_lbl": "📥 DROP SINGLE IMAGES OR ENTIRE IMAGE FOLDER HERE FOR FREE NEURAL CENTERING",
        "loaded_lbl": "📊 Consolidated image queue assets: {} items",
        "clear_btn": "🗑 Clear & Reset Queue",
        "btn_lbl": "🚀 One-Click Quick Export Centered Photos",
        "processing": "⏳ Neural pipeline processing asset {} / {}...",
        "success": "### ✅ Pipeline Render Completed! Total {} assets compiled in cloud disk!",
        "dl_btn": "🎁 Unlock & Download Centering Assets Package (ZIP)",
        "limit_err": "🔒 DEPLOYMENT PACK LOCKED ── Free trial quota cap exceeded (Max 10 Credits/24H). Please sign in or purchase token packages below to unlock high-res ZIP package immediately.",
        "usage_title": "📊 PREMIUM WORKSPACE WALLET",
        "guest_info": "🕒 Unregistered Free Tier:\n* Daily Used: **{} / 10** Credits\n*(Resets every 24 hours)*",
        "welcome": "👋 Welcome, Premium Partner: **{}** ｜ 🪙 Wallet Balance: **{} Credits**"
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
        "param_header": "⚙️ AI最適化パラメータ設定 (キーボード手動入力対応)",
        "ratio_lbl": "出力後の商品主体の表示比率 (10-99%):",
        "size_lbl": "出力画像の最大容量制限 (MB):",
        "drag_lbl": "📥 画像またはフォルダをここにドラッグ＆ドロップ (超巨大ドロップゾーン、無料トライアル対応)",
        "loaded_lbl": "📊 読み込まれた画像：{} 枚",
        "clear_btn": "🗑 キューをクリア",
        "btn_lbl": "🚀 ワンクリックで中央配置画像を高速エクスポート",
        "processing": "⏳ 解析中：第 {} 枚 / 全 {} 枚...",
        "success": "### ✅ 解析完了！合計 {} 枚 of 画像がクラウドで生成されました！",
        "dl_btn": "🎁 パッケージを解鎖してダウンロード (ZIP)",
        "limit_err": "🔒 パッケージがロックされました ── 無料枠制限(1日10 Creditsまで)を超えました。右側でログインするか、トークンを購入してダウンロードしてください。",
        "usage_title": "📊 プレミアム会員ウォレット状況",
        "guest_info": "🕒 未登録の無料プラン:\n* 本日の使用量: **{} / 10** Credits\n*(24時間ごとに自動リセット)*",
        "welcome": "👋 お帰りなさい、プレミアムパートナー: **{}** ｜ 🪙 残りトークン: **{} Credits**"
    },# 👑 👑 👑 【3倍超巨型拖曳方框停機坪 ── CSS 航空級注入晶片】 👑 👑 👑
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
# 完美對齊您的意志：第一為繁中、第二為簡中，中間絕不夾雜日文，最順眼流暢！
lang = st.selectbox("🌐 Language Interface ｜ 多國語言切換晶片", ("繁體中文", "简体中文", "English", "日本語", "한국어", "ภาษาไทย", "Bahasa Melayu", "Bahasa Indonesia"), index=0)
L = LANG_MAP[lang]

# 👑 全球高級電商雙欄位大氣佈局：左邊放功能，右邊放會員註冊與計數看板
main_col, side_col = st.columns([0.72, 0.28], gap="large")

with side_col:
    st.markdown(f"### {L['usage_title']}")
    if not st.session_state.user_authenticated:
        # 📊 完美對齊！右側遊客計數面板 100% 隨語言秒級翻譯變動，拉高儲值誘惑力！
        st.info(L["guest_info"].format(st.session_state.daily_usage))
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
    # 👑 大白話誠實標題完美對齊！
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

    uploaded_files = st.file_uploader(L["drag_lbl"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(L["clear_btn"], use_container_width=True, key="clear_all_queue"):
            st.rerun()
    with col_btn2:
        # 👑 完美鎖死：按鈕文字已 100% 同步修正為低調專業誠實的「一鍵快速導出完美置中商品照片」！
        start_btn = st.button(L["btn_lbl"], type="primary", use_container_width=True, key="start_pipeline")

    # 👑 👑 👑 【全域安全路徑對齊防線】 👑 👑 👑
    # 將 zip_path 高高宣告在最外層，即使網頁因為點擊下載而二度 Rerun 刷新，變數指針永不丟失！100% 杜絕錯誤！
    zip_path = "/tmp/processed_centered_images.zip"

    if uploaded_files:
        st.success(L["loaded_lbl"].format(len(uploaded_files)))
        
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
                status_text.markdown(L["processing"].format(idx, len(uploaded_files)))
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
                progress_bar.progress(idx / len(uploaded_files))
            
            if saved > 0:
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for root, _, files in os.walk(temp_out_dir):
                        for f in files: zip_file.write(os.path.join(root, f), f)
                st.session_state.compiled_saved = saved
                st.session_state.temp_ready = True
                st.success(L["success"].format(saved))
                
        # 🔒 下載防禦保險絲 ── 1原圖扣1點與遊客大防線
        if "temp_ready" in st.session_state and st.session_state.temp_ready and os.path.exists(zip_path):
            zip_file_size = os.path.getsize(zip_path)
            if zip_file_size > 0:
                with open(zip_path, "rb") as f_zip:
                    zip_data = f_zip.read()
                    
                if not user_authed:
                    if st.session_state.daily_usage + len(uploaded_files) > 10:
                        st.error(L["limit_err"])
                    else:
                        if st.download_button(label=L["dl_btn"], data=zip_data, file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True, key="dl_zip_btn_guest"):
                            st.session_state.daily_usage += len(uploaded_files)
                            st.session_state.temp_ready = False
                            st.rerun()
                else:
                    if user_credits_val < len(uploaded_files):
                        st.error(L["limit_err"])
                    else:
                        if st.download_button(label=L["dl_btn"], data=zip_data, file_name="processed_centered_images.zip", mime="application/zip", use_container_width=True, key="dl_zip_btn_user"):
                            new_balance = max(0, user_credits_val - len(uploaded_files))
                            if db and user_uid:
                                db.collection("users").document(user_uid).update({"credits": new_balance})
                            st.session_state.temp_ready = False
                            st.rerun()
