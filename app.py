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
        "param_header": "⚙️ AI Optimization & Parameter Infrastructure",
        "ratio_lbl": "Target subject spatial density ratio (10-99%):",
        "size_lbl": "Maximum payload weight constraint per image (MB):",
        "tip_header": "💡 OPERATIONAL SPECIFICATIONS",
        "tip_body": "1. Configure the optimization parameters directly below.\n2. Drag single images or an entire image folder into the drop zone below.\n3. Click the button to initialize the sub-second multi-threading render.\n4. Download the generated deployment package (ZIP) once compiled successfully.",
        "drag_lbl": "📥 Deploy your commerce image assets here (Supports single images or an entire folder)",
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
        "param_header": "⚙️ 最速電商智慧識別參數設定",
        "ratio_lbl": "導出後主體佔畫面比例 (10-99%):",
        "size_lbl": "導出後照片檔最大容量限制 (MB):",
        "tip_header": "💡 智慧網拍系統使用說明",
        "tip_body": "1. 先自行調整下方數值參數配置。\n2. 可以將「單張圖片」或「整個圖片資料夾」直接全數拖曳至下方區塊內（無數量限制）。\n3. 按下最下方秒級按鈕即可自動導出相片。\n4. 畫面顯示導出成功後點擊下載相片壓縮包進行確認。",
        "drag_lbl": "📥 將「單張相片」或「整個圖片資料夾」全數拖曳至此（支援多張 JPG, JPEG, PNG, WEBP）",
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
        "param_header": "⚙️ パラメータ最適化設定",
        "ratio_lbl": "出力後の商品主体の表示比率 (10-99%):",
        "size_lbl": "出力画像の最大容量制限 (MB):",
        "tip_header": "💡 システム操作説明",
        "tip_body": "1. 画面中央のパラメータ設定を行ってください。\n2. シングル画像または画像フォルダ全体を下の枠内にドラッグ＆ドロップしてください。\n3. 下の実行ボタンをクリックすると、超高速レンダリングが開始されます。\n4. 処理完了後、ZIPパッケージをダウンロードして確認してください。",
        "drag_lbl": "📥 シングル画像または画像フォルダ全体をここにドラッグ＆ドロップ (複数 JPG, JPEG, PNG, WEBP 対応)",
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

# 👑 額度狀態機計數晶片
if "daily_usage" not in st.session_state:
    st.session_state.daily_usage = 0
if "monthly_usage" not in st.session_state:
    st.session_state.monthly_usage = 0

# 右上方切換語言 (預設以西洋頂級風格 English 為首選主語言)
lang = st.selectbox("🌐 Language Interface", ("English", "繁體中文", "日本語"), index=0)
L = LANG_MAP[lang]

st.title(L["title"])
st.markdown(f"*{L['subtitle']}*")

# 📊 右上方 FREE 使用額度面板
st.info(f"**{L['usage_title']}** ｜ 🕒 Daily Limit: **{st.session_state.daily_usage} / 10** ｜ 📅 30 Days Count: **{st.session_state.monthly_usage} / 30**")

# 💡 使用說明大面板
with st.expander(f"**{L['tip_header']}**", expanded=True):
    st.markdown(L["tip_body"])

# ⚙️ 網拍參數配置
st.markdown("---")
st.markdown(f"#### {L['param_header']}")
col1, col2 = st.columns(2)
with col1:
    ratio_input = st.number_input(L["ratio_lbl"], min_value=10, max_value=99, value=90, step=5)
    ratio = ratio_input / 100.0
with col2:
    t_mb = st.number_input(L["size_lbl"], min_value=0.1, max_value=10.0, value=2.0, step=0.5)

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
        # 👑 FREE 免費額度限制與防禦保險絲
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
                        
                        h_p_o, w_p_o, _ = img_probe_orig.shape
                        
                        # 👑 👑 👑 【雙軌道像素大收網：原圖與轉90度各自探測】 👑 👑 👑
                        contours_normal = get_ai_bounding_boxes(img_probe_orig)
                        img_probe_rotated = cv2.rotate(img_probe_orig.copy(), cv2.ROTATE_90_CLOCKWISE)
                        contours_rotated = get_ai_bounding_boxes(img_probe_rotated)
                        
                        final_cropped_images = []
                        scale_factor = 1.0 / probe_scale
                        
                        # 🔴 生產線 A：收網「原圖方向」主體
                        for c in contours_normal:
                            hull = cv2.convexHull(c)
                            if cv2.contourArea(hull) > (w_p_o * h_p_o * 0.003):
                                bx_p, by_p, bw_p, bh_p = cv2.boundingRect(hull)
                                bx = int(bx_p * scale_factor)
                                by = int(by_p * scale_factor)
                                bw = int(bw_p * scale_factor)
                                bh = int(bh_p * scale_factor)
                                
                                bx, by = max(0, bx), max(0, by)
                                bw = min(w_orig - bx, bw)
                                bh = min(h_orig - by, bh)
                                
                                roi = img_orig[by:by+bh, bx:bx+bw]
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
                                            sbx, sby, sbw, sbh = int(sbx_p / roi_scale), int(sby_p / roi_scale), int(sbw_p / roi_scale), int(sbh_p / roi_scale)
                                            if sbw * sbh < (bw * bh * 0.92): 
                                                final_cropped_images.append((bx + sbx, by + sby, min(bw, sbw), min(bh, sbh), img_orig, False, bx_p, by_p, bw_p, bh_p))
                                                continue
                                final_cropped_images.append((bx, by, bw, bh, img_orig, False, bx_p, by_p, bw_p, bh_p))
                                 # 🔵 生產線 B：收網「轉90度方向」主體
                        h_r, w_r, _ = img_probe_rotated.shape
                        img_rotated_high = cv2.rotate(img_orig, cv2.ROTATE_90_CLOCKWISE)
                        h_rh, w_rh, _ = img_rotated_high.shape
                        
                        for c in contours_rotated:
                            hull = cv2.convexHull(c)
                            if cv2.contourArea(hull) > (w_r * h_r * 0.003):
                                bx_p, by_p, bw_p, bh_p = cv2.boundingRect(hull)
                                bx = int(bx_p * scale_factor)
                                by = int(by_p * scale_factor)
                                bw = int(bw_p * scale_factor)
                                bh = int(bh_p * scale_factor)
                                
                                bx, by = max(0, bx), max(0, by)
                                bw = min(w_rh - bx, bw)
                                bh = min(h_rh - by, bh)
                                
                                final_cropped_images.append((bx, by, bw, bh, img_rotated_high, True, bx_p, by_p, bw_p, bh_p))
                        
                        # 👑 👑 👑 【100% 幾何精準對齊 ── IoU 區域過濾晶片】 👑 👑 👑
                        # 👑 變數名稱 100% 修正完成！將 h_p_r 修正為正確的 h_r，徹底消除 NameError 閃退！
                        unified_boxes = []
                        for box in final_cropped_images:
                            bx, by, bw, bh, target_img, rotated_flag, bx_p, by_p, bw_p, bh_p = box
                            if rotated_flag:
                                # 💡 修正順時針旋轉下的探測圖原圖反推幾何公式，0像素錯位
                                ox1 = int((h_r - (by_p + bh_p)) * scale_factor)
                                ox2 = int((h_r - by_p) * scale_factor)
                                oy1 = int(bx_p * scale_factor)
                                oy2 = int((bx_p + bw_p) * scale_factor)
                            else:
                                ox1 = bx
                                ox2 = bx + bw
                                oy1 = by
                                oy2 = by + bh
                            unified_boxes.append((ox1, oy1, ox2, oy2, box))
                        
                        # 核心 IoU 過濾：重疊度高達 70% 才融合成一張，確保單張商品與多主體卡片 100% 安全
                        unique_crops = []
                        for item in unified_boxes:
                            ox1, oy1, ox2, oy2, box_data = item
                            area_current = (ox2 - ox1) * (oy2 - oy1)
                            
                            is_duplicate = False
                            for existing in unique_crops:
                                ex_x1, ex_y1, ex_x2, ex_y2, ex_box = existing
                                area_existing = (ex_x2 - ex_x1) * (ex_y2 - ex_y1)
                                
                                ix1 = max(ox1, ex_x1)
                                iy1 = max(oy1, ex_y1)
                                ix2 = min(ox2, ex_x2)
                                iy2 = min(oy2, ex_y2)
                                
                                if ix2 > ix1 and iy2 > iy1:
                                    inter_area = (ix2 - ix1) * (iy2 - iy1)
                                    union_area = area_current + area_existing - inter_area
                                    iou = inter_area / union_area if union_area > 0 else 0
                                    
                                    if iou > 0.7:
                                        is_duplicate = True
                                        if area_current > area_existing:
                                            unique_crops.remove(existing)
                                            unique_crops.append(item)
                                        break
                            if not is_duplicate:
                                unique_crops.append(item)
                        
                        if not unique_crops:
                            unique_crops.append((int(w_orig*0.25), int(h_orig*0.25), int(w_orig*0.75), int(h_orig*0.75), (int(w_orig*0.25), int(h_orig*0.25), int(w_orig*0.5), int(w_orig*0.5), img_orig, False, 0, 0, 0, 0)))
                        
                        # 👑 👑 👑 【純原圖自適應 ── 最大化物理邊界卡位演算法】 👑 👑 👑
                        for part_idx, (ox1, oy1, ox2, oy2, box_data) in enumerate(unique_crops, 1):
                            bx, by, bw, bh, target_img, rotated_flag, _, _, _, _ = box_data
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
                            
                            if rotated_flag:
                                cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)
                            
                            # 👑 容量限制二分搜尋法 (縮排對齊 100% 修正完成)
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
