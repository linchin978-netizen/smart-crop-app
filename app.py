import os, io, zipfile, cv2, gc, numpy as np
from PIL import Image, ImageOps
from rembg import remove, new_session
import streamlit as st

# 👑 雲端快取優化：確保 AI 模型在雲端只載入一次，節省記憶體
@st.cache_resource
def load_rembg_session():
    return new_session("silueta")

session = load_rembg_session()

def get_ai_bounding_boxes(cv_img):
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
        "tip_body": "1. Directly type your optimization parameters below via keyboard.\n2. Drag single images or an entire image folder into the drop zone below.\n3. Click the button to initialize the sub-second multi-threading render.\n4. Download the generated deployment package (ZIP) once compiled successfully.",
        "drag_lbl": "📥 DROP SINGLE IMAGES OR ENTIRE IMAGE FOLDER HERE TO INITIALIZE NEURAL PIPELINE",
        "loaded_lbl": "📊 Consolidated image queue assets: {} items",
        "clear_btn": "🗑 Clear & Reset Queue",
        "btn_lbl": "⚡ Initialize Sub-Second Smart Centering Deployment",
        "processing": "⏳ Neural pipeline processing asset {} / {}...",
        "success": "### ✅ Pipeline Render Completed! Total {} assets deployed!",
        "dl_btn": "🎁 Download Compiled Centering Assets Package (ZIP)",
        "limit_err": "❌ Operational threshold exceeded! FREE quota tier is capped at 30 assets/daily and 60 assets/monthly.",
        "usage_title": "📊 FREE SYSTEM QUOTA STATUS"
    },
    "繁體中文": {
        "title": "⚡ NEXUS CROP — 頂級電商商品照智慧置中裁切系統",
        "subtitle": "新世代高精主體光學識別 ── 最速電商純原圖極限邊界雲端引擎",
        "param_header": "⚙️ 最速電商智慧識別參數設定 (支援鍵盤手動自行輸入)",
        "ratio_lbl": "導出後主體佔畫面比例 (10-99%):",
        "size_lbl": "導出後照片檔最大容量限制 (MB):",
        "tip_header": "💡 智慧網拍系統使用說明",
        "tip_body": "1. 點擊下方輸入框，可直接用鍵盤手動自行打字輸入數值。\n2. 可以將「單張圖片」或「整個圖片資料夾」直接全數拖曳至下方區塊內（無數量限制）。\n3. 按下最下方秒級按鈕即可自動導出相片。\n4. 畫面顯示導出成功後點擊下載相片壓縮包進行確認。",
        "drag_lbl": "📥 將「單張相片」或「整個圖片資料夾」全數拖曳至此巨型向量場中（支援多張 JPG, WEBP）",
        "loaded_lbl": "📊 目前已載入商品照片：{} 張",
        "clear_btn": "🗑 清除重選",
        "btn_lbl": "🚀 一鍵秒級導出完美置中商品照片",
        "processing": "⏳ 智慧光學解算中：第 {} 張 / 共 {} 張...",
        "success": "### ✅ 核心解算成功！共生成 {} 張智慧置中照片！",
        "dl_btn": "🎁 點擊一鍵下載完美置中相片壓縮包 (ZIP)",
        "limit_err": "❌ 已超過每日或每月免費額度！FREE用戶每日上限為 30 張，30天累計上限為 60 張。",
        "usage_title": "📊 FREE 免費額度智慧計數看板"
    },
    "日本語": {
        "title": "⚡ NEXUS CROP — AI 高速EC商品画像自動中央配置システム",
        "subtitle": "次世代オブジェクト認識テクノロジー ── 純粋画素境界クラウドエンジン",
        "param_header": "⚙️ パラメータ最適化設定 (キーボード手動入力対応)",
        "ratio_lbl": "出力後の商品主体の表示比率 (10-99%):",
        "size_lbl": "出力画像の最大容量制限 (MB):",
        "tip_header": "💡 システム操作説明",
        "tip_body": "1. 画面中央のボックスをクリックして、キーボードから手動で数値を入力してください。\n2. シングル画像または画像フォルダ全体を下の巨大な枠内にドラッグ＆ドロップしてください。\n3. 下の実行ボタンをクリックすると、超高速レンダリングが開始されます。\n4. 処理完了後、ZIPパッケージをダウンロードして確認してください。",
        "drag_lbl": "📥 シングル画像または画像フォルダ全体をここにドラッグ＆ドロップ (巨大なベクタードロップゾーン)",
        "loaded_lbl": "📊 読み込まれた商品画像：{} 枚",
        "clear_btn": "🗑 キューをクリア",
        "btn_lbl": "⚡ 完璧な中央配置画像をワンクリックでエクスポート",
        "processing": "⏳ クラウド解析中：第 {} 枚 / 全 {} 枚...",
        "success": "### ✅ クラウド解析完了！合計 {} 枚の画像が生成されました！",
        "dl_btn": "🎁 画像ZIPパッケージをダウンロード",
        "limit_err": "❌ 無料利用枠の制限を超えました！1日の上限は30枚、30日間の上限は60枚です。",
        "usage_title": "📊 FREE 無料制限枠の使用状況"
    }
}

st.set_page_config(page_title="NEXUS CROP — AI Edition", page_icon="⚡", layout="centered")

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
    [data-testid="stFileUploaderDropzone"] i {
        color: #3498db !important;
        transform: scale(1.5);
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)
# 👑 額度狀態機計數晶片
if "daily_usage" not in st.session_state:
    st.session_state.daily_usage = 0
if "monthly_usage" not in st.session_state:
    st.session_state.monthly_usage = 0

# 右上方切換語言
lang = st.selectbox("🌐 Language Interface", ("English", "繁體中文", "日本語"), index=0)
L = LANG_MAP[lang]

st.title(L["title"])
st.markdown(f"*{L['subtitle']}*")

# 📊 右上方 FREE 使用額度面板 (每日免費公測額度已放寬至 30 張！)
st.info(f"**{L['usage_title']}** ｜ 🕒 Daily Limit: **{st.session_state.daily_usage} / 30** ｜ 📅 30 Days Count: **{st.session_state.monthly_usage} / 60**")

# 💡 使用說明大面板
with st.expander(f"**{L['tip_header']}**", expanded=True):
    st.markdown(L["tip_body"])

# ⚙️ 網拍參數配置面板 (解鎖鍵盤自由手動輸入)
st.markdown("---")
st.markdown(f"#### {L['param_header']}")
col1, col2 = st.columns(2)
with col1:
    ratio_str = st.text_input(L["ratio_lbl"], value="90")
    try:
        ratio_val = float(ratio_str)
        ratio = max(10.0, min(99.0, ratio_val)) / 100.0
    except:
        ratio = 0.90  # 防呆兜底
with col2:
    size_str = st.text_input(L["size_lbl"], value="2.0")
    try:
        t_mb = max(0.1, float(size_str))
    except:
        t_mb = 2.0  # 防呆兜底

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

uploaded_files = st.file_uploader(L["drag_lbl"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key=f"uploader_{st.session_state.uploader_key}")

# 🗑 清除重選按鈕與一鍵秒級導出按鈕佈局面板
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button(L["clear_btn"], use_container_width=True):
        st.session_state.uploader_key += 1
        st.rerun()

with col_btn2:
    start_btn = st.button(L["btn_lbl"], type="primary", use_container_width=True)

if uploaded_files:
    st.success(L["loaded_lbl"].format(len(uploaded_files)))
    
    if start_btn:
        if st.session_state.daily_usage + len(uploaded_files) > 30 or st.session_state.monthly_usage + len(uploaded_files) > 60:
            st.error(L["limit_err"])
        else:
            zip_buffer = io.BytesIO()
            saved = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for idx, file in enumerate(uploaded_files, 1):
                    status_text.markdown(L["processing"].format(idx, len(uploaded_files)))
                    
                    try:
                        # 👑 100% 採用與桌面版同級的「照妖鏡硬解」上游機制
                        bytes_data = file.read()
                        pil_img = Image.open(io.BytesIO(bytes_data))
                        pil_img = ImageOps.exif_transpose(pil_img) 
                        img_orig = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                        
                        h_orig, w_orig, _ = img_orig.shape
                        
                        # 👑 👑 👑 【2K 級高精細光學探測盾 ── 提升極限至 2000 像素！】 👑 👑 👑
                        # 徹底消除特徵稀釋漏洞！留住右轉90度發光聖誕樹的所有細節，將全黑大樹跟橙色建物當場抹除！
                        probe_scale = 1.0
                        if w_orig > 2000:
                            probe_scale = 2000.0 / w_orig
                            w_probe = 2000
                            h_probe = int(h_orig * probe_scale)
                            img_probe_orig = cv2.resize(img_orig, (w_probe, h_probe), interpolation=cv2.INTER_AREA)
                        else:
                            img_probe_orig = img_orig.copy()
                        
                        h_p_o, w_p_o, _ = img_probe_orig.shape
                        
                        # 👑 100% 桌面版商品計數決策大腦
                        contours_0 = get_ai_bounding_boxes(img_probe_orig)
                        img_probe_90 = cv2.rotate(img_probe_orig.copy(), cv2.ROTATE_90_CLOCKWISE)
                        contours_90 = get_ai_bounding_boxes(img_probe_90)
                        img_probe_180 = cv2.rotate(img_probe_orig.copy(), cv2.ROTATE_180)
                        contours_180 = get_ai_bounding_boxes(img_probe_180)
                        img_probe_270 = cv2.rotate(img_probe_orig.copy(), cv2.ROTATE_90_COUNTERCLOCKWISE)
                        contours_270 = get_ai_bounding_boxes(img_probe_270)
                        
                        valid_cnt_0 = sum(1 for c in contours_0 if cv2.contourArea(cv2.convexHull(c)) > (w_p_o * h_p_o * 0.015))
                        h_p_90, w_p_90, _ = img_probe_90.shape
                        valid_cnt_90 = sum(1 for c in contours_90 if cv2.contourArea(cv2.convexHull(c)) > (w_p_90 * h_p_90 * 0.015))
                        h_p_180, w_p_180, _ = img_probe_180.shape
                        valid_cnt_180 = sum(1 for c in contours_180 if cv2.contourArea(cv2.convexHull(c)) > (w_p_180 * h_p_180 * 0.015))
                        h_p_270, w_p_270, _ = img_probe_270.shape
                        valid_cnt_270 = sum(1 for c in contours_270 if cv2.contourArea(cv2.convexHull(c)) > (w_p_270 * h_p_270 * 0.015))
                        max_cnt = max(valid_cnt_0, valid_cnt_90, valid_cnt_180, valid_cnt_270)
                        
                        if max_cnt == valid_cnt_90 and valid_cnt_90 > valid_cnt_0:
                            img = cv2.rotate(img_orig, cv2.ROTATE_90_CLOCKWISE)
                            contours = contours_90
                            rotation_mode = 90
                            is_rotated_for_calculation = True
                        elif max_cnt == valid_cnt_180 and valid_cnt_180 > valid_cnt_0:
                            img = cv2.rotate(img_orig, cv2.ROTATE_180)
                            contours = contours_180
                            rotation_mode = 180
                            is_rotated_for_calculation = True
                        elif max_cnt == valid_cnt_270 and valid_cnt_270 > valid_cnt_0:
                            img = cv2.rotate(img_orig, cv2.ROTATE_90_COUNTERCLOCKWISE)
                            contours = contours_270
                            rotation_mode = 270
                            is_rotated_for_calculation = True
                        else:
                            img = img_orig
                            contours = contours_0
                            rotation_mode = 0
                            is_rotated_for_calculation = False

                        h_high, w_high, _ = img.shape
                        scale_factor = 1.0 / probe_scale
                        valid_boxes = []
                        
                        for c in contours:
                            hull = cv2.convexHull(c)
                            if cv2.contourArea(hull) > ((w_high * probe_scale) * (h_high * probe_scale) * 0.015):
                                bx_p, by_p, bw_p, bh_p = cv2.boundingRect(hull)
                                bx = int(bx_p * scale_factor)
                                by = int(by_p * scale_factor)
                                bw = int(bw_p * scale_factor)
                                bh = int(bh_p * scale_factor)
                                
                                bx, by = max(0, bx), max(0, by)
                                bw = min(w_high - bx, bw)
                                bh = min(h_high - by, bh)
                                
                                roi = img[by:by+bh, bx:bx+bw]
                                if roi.size > 0:
                                    g_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                                    e_roi = cv2.Canny(g_roi, 50, 150)
                                    if (np.sum(e_roi > 0) / e_roi.size) < 0.05:
                                        roi_h, roi_w, _ = roi.shape
                                        roi_scale = 500.0 / roi_w if roi_w > 500 else 1.0
                                        roi_probe = cv2.resize(roi, (500, int(roi_h * roi_scale)), interpolation=cv2.INTER_AREA) if roi_w > 500 else roi.copy()
                                        s_pil = remove(Image.fromarray(cv2.cvtColor(roi_probe, cv2.COLOR_BGR2RGB)), session=session)
                                        s_alpha = cv2.cvtColor(np.array(s_pil), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                                        _, s_thresh = cv2.threshold(s_alpha, 10, 255, cv2.THRESH_BINARY)
                                        s_cnt, _ = cv2.findContours(s_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                                        if s_cnt:
                                            sbx_p, sby_p, sbw_p, sbh_p = cv2.boundingRect(max(s_cnt, key=cv2.contourArea))
                                            sbx, sby, sbw, bh_new = int(sbx_p / roi_scale), int(sby_p / roi_scale), int(sbw_p / roi_scale), int(sbh_p / roi_scale)
                                            if sbw * bh_new < (bw * bh * 0.92): 
                                                valid_boxes.append((bx + sbx, by + sby, min(bw, sbw), min(bh, bh_new)))
                                                continue
                                valid_boxes.append((bx, by, bw, bh))
                        
                        if not valid_boxes:
                            valid_boxes.append((int(w_high*0.25), int(w_high*0.25), int(w_high*0.5), int(w_high*0.5)))
                        
                        # 👑 👑 👑 【100% 刀跟肉身對齊 ── 完美置中】 👑 👑 👑
                        for part_idx, (bx, by, bw, bh) in enumerate(valid_boxes, 1):
                            cx, cy = bx + bw // 2, by + bh // 2
                            
                            ideal_pad_w = int((bw / ratio - bw) / 2)
                            ideal_pad_h = int((bh / ratio - bh) / 2)
                            
                            pad_l = min(cx - bw // 2, ideal_pad_w)
                            pad_r = min((w_high - cx) - bw // 2, ideal_pad_w)
                            pad_t = min(cy - bh // 2, ideal_pad_h)
                            pad_b = min((h_high - cy) - bh // 2, ideal_pad_h)
                            
                            x1 = max(0, cx - bw // 2 - pad_l)
                            x2 = min(w_high, cx + bw // 2 + pad_r)
                            y1 = max(0, cy - bh // 2 - pad_t)
                            y2 = min(h_high, cy + bh // 2 + pad_b)
                            
                            cropped = img[y1:y2, x1:x2]
                            if cropped.size == 0: continue
                            
                            if is_rotated_for_calculation:
                                if rotation_mode == 90: cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)
                                elif rotation_mode == 180: cropped = cv2.rotate(cropped, cv2.ROTATE_180)
                                elif rotation_mode == 270: cropped = cv2.rotate(cropped, cv2.ROTATE_90_CLOCKWISE)
                            
                            t_bytes = t_mb * 1024 * 1024; low, high, best_q = 1, 100, 85
                            for _ in range(10):
                                mid = (low + high) // 2
                                _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, mid])
                                if len(buf) <= t_bytes: best_q = mid; low = mid + 1
                                else: high = mid - 1
                            _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, best_q])
                            
                            base_name, _ = os.path.splitext(file.name)
                            out_img_name = f"{base_name}_{part_idx}.jpg" if len(valid_boxes) > 1 else f"{base_name}.jpg"
                            zip_file.writestr(out_img_name, buf.tobytes())
                            saved += 1
                            
                        # 👑 26張大上傳免斷電垃圾強制回收
                        del img, img_orig, img_probe_orig, contours, contours_0, contours_90, contours_180, contours_270
                        gc.collect()
                            
                    except Exception as e:
                        st.error(f"Error {file.name}: {str(e)}")
                    
                    progress_bar.progress(idx / len(uploaded_files))
            
            # 下載按鈕外嵌大防線
            st.session_state.daily_usage += len(uploaded_files)
            st.session_state.monthly_usage += len(uploaded_files)
            st.success(L["success"].format(saved))
            
            zip_buffer.seek(0)
            st.download_button(
                label=L["dl_btn"],
                data=zip_buffer,
                file_name="processed_centered_images.zip",
                mime="application/zip",
                use_container_width=True
            )
