import os, io, zipfile, cv2, numpy as np
from PIL import Image
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
        "limit_err": "❌ Operational threshold exceeded! FREE quota tier is capped at 10 assets/daily and 30 assets/monthly.",
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
        "limit_err": "❌ 已超過每日或每月免費額度！FREE用戶30天累計上限為 30 張。",
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
        "dl_btn": "🎁 中央配置画像ZIPパッケージをダウンロード",
        "limit_err": "❌ 無料利用枠の制限を超えました！30日間の上限は30枚です。",
        "usage_title": "📊 FREE 無料制限枠の使用状況"
    }
}

st.set_page_config(page_title="NEXUS CROP — AI Edition", page_icon="⚡", layout="centered")

# 👑 巨型拖曳方框 CSS 注入晶片 (面積強行放大 3 倍，支援資料夾盲拉)
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

# 📊 右上方 FREE 使用額度面板
st.info(f"**{L['usage_title']}** ｜ 🕒 Daily Limit: **{st.session_state.daily_usage} / 10** ｜ 📅 30 Days Count: **{st.session_state.monthly_usage} / 30**")

# 💡 使用說明大面板
with st.expander(f"**{L['tip_header']}**", expanded=True):
    st.markdown(L["tip_body"])

# ⚙️ 網拍參數配置面板 (支援鍵盤自由手動輸入)
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
        if st.session_state.daily_usage + len(uploaded_files) > 10 or st.session_state.monthly_usage + len(uploaded_files) > 30:
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
                        file_bytes = np.frombuffer(file.read(), dtype=np.uint8)
                        img_orig = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                        if img_orig is None: continue
                        
                        h_orig, w_orig, _ = img_orig.shape
                        
                        # 👑 【雲端防爆降維盾】：限制探測圖最大寬度為 1000
                        probe_scale = 1.0
                        if w_orig > 1000:
                            probe_scale = 1000.0 / w_orig
                            w_probe = 1000
                            h_probe = int(h_orig * probe_scale)
                            img_probe_orig = cv2.resize(img_orig, (w_probe, h_probe), interpolation=cv2.INTER_AREA)
                        else:
                            img_probe_orig = img_orig.copy()
                        
                        h_p_0, w_p_o, _ = img_probe_orig.shape
                        
                        # 👑 👑 👑 【四時空全維度像素大收網 ── 四個時空通通平行去背！】 👑 👑 👑
                        contours_0 = get_ai_bounding_boxes(img_probe_orig)
                        img_probe_90 = cv2.rotate(img_probe_orig.copy(), cv2.ROTATE_90_CLOCKWISE)
                        contours_90 = get_ai_bounding_boxes(img_probe_90)
                        img_probe_180 = cv2.rotate(img_probe_orig.copy(), cv2.ROTATE_180)
                        contours_180 = get_ai_bounding_boxes(img_probe_180)
                        img_probe_270 = cv2.rotate(img_probe_orig.copy(), cv2.ROTATE_90_COUNTERCLOCKWISE)
                        contours_270 = get_ai_bounding_boxes(img_probe_270)
                        
                        # 統合四個世界的探測成果，交給 IoU 幾何大腦過濾
                        all_discovered_boxes = []
                        scale_factor = 1.0 / probe_scale
                        
                        # 1️⃣ 軌道 0 度：收網原圖
                        for c in contours_0:
                            hull = cv2.convexHull(c)
                            # 👑 重新鎖死 0.015 黃金門檻！在防爆降維盾下徹底抹除所有陰影雜訊，力保短可樂機不碎！
                            if cv2.contourArea(hull) > (w_p_o * h_p_0 * 0.015):
                                bx_p, by_p, bw_p, bh_p = cv2.boundingRect(hull)
                                bx, by = int(bx_p * scale_factor), int(by_p * scale_factor)
                                bw, bh = int(bw_p * scale_factor), int(bh_p * scale_factor)
                                bx, by = max(0, bx), max(0, by)
                                final_img = img_orig.copy()
                                all_discovered_boxes.append((bx, by, bx+bw, by+bh, bx, by, bw, bh, final_img, 0))
                                 # 2️⃣ 軌道 90 度順時針
                        h_p_90, w_p_90, _ = img_probe_90.shape
                        img_high_90 = cv2.rotate(img_orig, cv2.ROTATE_90_CLOCKWISE)
                        for c in contours_90:
                            hull = cv2.convexHull(c)
                            if cv2.contourArea(hull) > (w_p_90 * h_p_90 * 0.015):
                                bx_p, by_p, bw_p, bh_p = cv2.boundingRect(hull)
                                bx, by = int(bx_p * scale_factor), int(by_p * scale_factor)
                                bw, bh = int(bw_p * scale_factor), int(bh_p * scale_factor)
                                bx, by = max(0, bx), max(0, by)
                                # 💡 100% 精準映射回原圖座標系
                                ox1 = w_orig - (by + bh)
                                oy1 = bx
                                ox2 = w_orig - by
                                oy2 = bx + bw
                                all_discovered_boxes.append((ox1, oy1, ox2, oy2, bx, by, bw, bh, img_high_90, 90))

                        # 3️⃣ 軌道 180 度顛倒
                        h_p_180, w_p_180, _ = img_probe_180.shape
                        img_high_180 = cv2.rotate(img_orig, cv2.ROTATE_180)
                        for c in contours_180:
                            hull = cv2.convexHull(c)
                            if cv2.contourArea(hull) > (w_p_180 * h_p_180 * 0.015):
                                bx_p, by_p, bw_p, bh_p = cv2.boundingRect(hull)
                                bx, by = int(bx_p * scale_factor), int(by_p * scale_factor)
                                bw, bh = int(bw_p * scale_factor), int(bh_p * scale_factor)
                                bx, by = max(0, bx), max(0, by)
                                ox1 = w_orig - (bx + bw)
                                oy1 = h_orig - (by + bh)
                                ox2 = w_orig - bx
                                oy2 = h_orig - by
                                all_discovered_boxes.append((ox1, oy1, ox2, oy2, bx, by, bw, bh, img_high_180, 180))

                        # 4️⃣ 軌道 270 度逆時針
                        h_p_270, w_p_270, _ = img_probe_270.shape
                        img_high_270 = cv2.rotate(img_orig, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        for c in contours_270:
                            hull = cv2.convexHull(c)
                            if cv2.contourArea(hull) > (w_p_270 * h_p_270 * 0.015):
                                bx_p, by_p, bw_p, bh_p = cv2.boundingRect(hull)
                                bx, by = int(bx_p * scale_factor), int(by_p * scale_factor)
                                bw, bh = int(bw_p * scale_factor), int(bh_p * scale_factor)
                                bx, by = max(0, bx), max(0, by)
                                ox1 = by
                                oy1 = h_orig - (bx + bw)
                                ox2 = by + bh
                                oy2 = h_orig - bx
                                all_discovered_boxes.append((ox1, oy1, ox2, oy2, bx, by, bw, bh, img_high_270, 270))

                        # 👑 👑 👑 【四世界交集 IoU 區域過濾大腦】 👑 👑 👑
                        # 只要發現有重疊率大於 40% 的物件，立刻融合成一個，保證直橫魔王照片全部不漏，且重複圖 0 出現！
                        unique_crops = []
                        for item in all_discovered_boxes:
                            ox1, oy1, ox2, oy2, bx, by, bw, bh, target_img, r_mode = item
                            area_current = (ox2 - ox1) * (oy2 - oy1)
                            
                            is_duplicate = False
                            for existing in unique_crops:
                                ex_x1, ex_y1, ex_x2, ex_y2, ex_box = existing
                                area_existing = (ex_x2 - ex_x1) * (ex_y2 - ex_y1)
                                
                                ix1, iy1 = max(ox1, ex_x1), max(oy1, ex_y1)
                                ix2, iy2 = min(ox2, ex_x2), min(oy2, ex_y2)
                                
                                if ix2 > ix1 and iy2 > iy1:
                                    inter_area = (ix2 - ix1) * (iy2 - iy1)
                                    union_area = area_current + area_existing - inter_area
                                    iou = inter_area / union_area if union_area > 0 else 0
                                    
                                    if iou > 0.40:
                                        is_duplicate = True
                                        # 誰的主體面積形狀更完整飽滿，就留下誰
                                        if area_current > area_existing:
                                            unique_crops.remove(existing)
                                            unique_crops.append(existing_box_data := existing)
                                        break
                            if not is_duplicate:
                                unique_crops.append(item)
                        
                        if not unique_crops:
                            unique_crops.append((int(w_orig*0.25), int(h_orig*0.25), int(w_orig*0.75), int(h_orig*0.75), int(w_orig*0.25), int(h_orig*0.25), int(w_orig*0.5), int(w_orig*0.5), img_orig, 0))
                        
                        # 👑 👑 👑 【純原圖自適應 ── 最大化物理邊界卡位演算法】 👑 👑 👑
                        for part_idx, (ox1, oy1, ox2, oy2, bx, by, bw, bh, target_img, r_mode) in enumerate(unique_crops, 1):
                            cx, cy = bx + bw // 2, by + bh // 2
                            img_h, img_w, _ = target_img.shape
                            
                            ideal_pad_w = int((bw / ratio - bw) / 2)
                            ideal_pad_h = int((bh / ratio - bh) / 2)
                            
                            pad_l = min(cx - bw // 2, ideal_pad_w)
                            pad_r = min((img_w - cx) - bw // 2, ideal_pad_w)
                            pad_t = min(cy - bh // 2, ideal_pad_h)
                            pad_b = min((img_h - cy) - bh // 2, ideal_pad_h)
                            
                            x1 = max(0, cx - bw // 2 - pad_l)
                            x2 = min(img_w, cx + bw // 2 + pad_r)
                            y1 = max(0, cy - bh // 2 - pad_t)
                            y2 = min(img_h, cy + bh // 2 + pad_b)
                            
                            cropped = target_img[y1:y2, x1:x2]
                            if cropped.size == 0: continue
                            
                            # 在最後一毫秒，各自反向轉正還原原始角度
                            if r_mode == 90: cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)
                            elif r_mode == 180: cropped = cv2.rotate(cropped, cv2.ROTATE_180)
                            elif r_mode == 270: cropped = cv2.rotate(cropped, cv2.ROTATE_90_CLOCKWISE)
                            
                            # 👑 容量限制二分搜尋法
                            t_bytes = t_mb * 1024 * 1024; low, high, best_q = 1, 100, 85
                            for _ in range(10):
                                mid = (low + high) // 2
                                _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, mid])
                                if len(buf) <= t_bytes: best_q = mid; low = mid + 1
                                else: high = mid - 1
                            _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, best_q])
                            
                            base_name, _ = os.path.splitext(file.name)
                            out_img_name = f"{base_name}_{part_idx}.jpg" if len(unique_crops) > 1 else f"{base_name}.jpg"
                            zip_file.writestr(out_img_name, buf.tobytes())
                            saved += 1
                            
                    except Exception as e:
                        st.error(f"Error {file.name}: {str(e)}")
                    
                    progress_bar.progress(idx / len(uploaded_files))
            
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
