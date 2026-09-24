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
    """100% 純血原版 A 去背，此處傳入的是經過輕量化的影像"""
    img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    output_pil = remove(Image.fromarray(img_rgb), session=session)
    alpha = cv2.cvtColor(np.array(output_pil), cv2.COLOR_RGBA2BGRA)[:, :, 3]
    _, thresh = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

# 🎯 網頁介面視覺包裝
st.set_page_config(page_title="網拍置中裁切 ── 智慧雲端收費版", page_icon="🚀", layout="centered")
st.title("🚀 智慧網拍商品照自動置中裁切系統")
st.markdown("### (張三丰太極盲測 ── 雲端不爆記憶體安全版)")

# 📥 參數配置面版
st.sidebar.header("⚙️ 網拍上架參數優化設定")
ratio_input = st.sidebar.number_input("導出後主體佔畫面比例 (10-99%):", min_value=10, max_value=99, value=90, step=5)
t_mb = st.sidebar.number_input("導出後照片檔最大容量限制 (MB):", min_value=0.1, max_value=10.0, value=2.0, step=0.5)
ratio = ratio_input / 100.0

# 📥 網頁拖曳上傳方框
uploaded_files = st.file_uploader("📥 將欲編輯的網拍照片全數拖曳至此 (支援多張 JPG, JPEG, PNG, WEBP)", 
                                  type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
if uploaded_files:
    st.success(f"📊 目前已載入商品照片：{len(uploaded_files)} 張")
    
    if st.button("🚀 開始秒級一鍵導出完美置中商品照"):
        zip_buffer = io.BytesIO()
        saved = 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, file in enumerate(uploaded_files, 1):
                status_text.markdown(f"⏳ 雲端高質量解算中：第 {idx} 張 / 共 {len(uploaded_files)} 張...")
                
                try:
                    # 讀取最完整的高畫質原始肉身
                    file_bytes = np.frombuffer(file.read(), dtype=np.uint8)
                    img_orig = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                    if img_orig is None: continue
                    
                    h_orig, w_orig, _ = img_orig.shape
                    
                    # 👑 【雲端防爆降維盾】：限制探測圖的最大寬度為 1000，防止雲端記憶體被撐爆！
                    probe_scale = 1.0
                    if w_orig > 1000:
                        probe_scale = 1000.0 / w_orig
                        w_probe = 1000
                        h_probe = int(h_orig * probe_scale)
                        img_probe_orig = cv2.resize(img_orig, (w_probe, h_probe), interpolation=cv2.INTER_AREA)
                    else:
                        img_probe_orig = img_orig.copy()
                    
                    # 👑 👑 👑 【輕量化 ── AI 像素級盲測大腦】 👑 👑 👑
                    # 用輕量圖跑原圖方向去背
                    contours_normal = get_ai_bounding_boxes(img_probe_orig)
                    
                    # 用輕量圖跑旋轉90度去背
                    img_probe_rotated = cv2.rotate(probe_img_target := img_probe_orig.copy(), cv2.ROTATE_90_CLOCKWISE)
                    contours_rotated = get_ai_bounding_boxes(probe_img_target)
                    
                    h_p_o, w_p_o, _ = img_probe_orig.shape
                    valid_cnt_normal = sum(1 for c in contours_normal if cv2.contourArea(cv2.convexHull(c)) > (w_p_o * h_p_o * 0.015))
                    
                    h_p_r, w_p_r, _ = img_probe_rotated.shape
                    valid_cnt_rotated = sum(1 for c in contours_rotated if cv2.contourArea(cv2.convexHull(c)) > (w_p_r * h_p_r * 0.015))
                    
                    # 決策分流：判定是否為轉動錯位的相片
                    if valid_cnt_rotated > valid_cnt_normal:
                        # 核心計算走旋轉世界，但這時我們同步把「高畫質原圖」翻轉，座標依然完美對齊！
                        img = cv2.rotate(img_orig, cv2.ROTATE_90_CLOCKWISE)
                        contours = contours_rotated
                        is_rotated_for_calculation = True
                        scale_factor = 1.0 / probe_scale # 反推回高畫質原圖的比例放大係數
                    else:
                        img = img_orig
                        contours = contours_normal
                        is_rotated_for_calculation = False
                        scale_factor = 1.0 / probe_scale
                    
                    h_high, w_high, _ = img.shape
                    valid_boxes = []
                    
                    # 100% 鎖死原版 A 的 0.015 黃金大門檻
                    for c in contours:
                        hull = cv2.convexHull(c)
                        if cv2.contourArea(hull) > ((w_high * probe_scale) * (h_high * probe_scale) * 0.015):
                            # 將輕量探測圖抓到的 Bounding Box，精準等比例「放大對齊」到高畫質原圖上！
                            bx_p, by_p, bw_p, bh_p = cv2.boundingRect(hull)
                            bx = int(bx_p * scale_factor)
                            by = int(by_p * scale_factor)
                            bw = int(bw_p * scale_factor)
                            bh = int(bh_p * scale_factor)
                            
                            # 邊界安全邊緣防止越界
                            bx, by = max(0, bx), max(0, by)
                            bw = min(w_high - bx, bw)
                            bh = min(h_high - by, bh)
                            
                            roi = img[by:by+bh, bx:bx+bw]
                            if roi.size > 0:
                                g_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                                e_roi = cv2.Canny(g_roi, 50, 150)
                                if (np.sum(e_roi > 0) / e_roi.size) < 0.05:
                                    # 局部二次去背，同樣對 ROI 進行雲端降維防爆保護
                                    roi_h, roi_w, _ = roi.shape
                                    roi_scale = 1.0
                                    if roi_w > 500:
                                        roi_scale = 500.0 / roi_w
                                        roi_probe = cv2.resize(roi, (500, int(roi_h * roi_scale)), interpolation=cv2.INTER_AREA)
                                    else:
                                        roi_probe = roi.copy()
                                        
                                    s_pil = remove(Image.fromarray(cv2.cvtColor(roi_probe, cv2.COLOR_BGR2RGB)), session=session)
                                    s_alpha = cv2.cvtColor(np.array(s_pil), cv2.COLOR_RGBA2BGRA)[:, :, 3]
                                    _, s_thresh = cv2.threshold(s_alpha, 10, 255, cv2.THRESH_BINARY)
                                    s_cnt, _ = cv2.findContours(s_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                                    if s_cnt:
                                        sbx_p, sby_p, sbw_p, sbh_p = cv2.boundingRect(max(s_cnt, key=cv2.contourArea))
                                        sbx = int(sbx_p / roi_scale)
                                        sby = int(sby_p / roi_scale)
                                        sbw = int(sbw_p / roi_scale)
                                        sbh = int(sbh_p / roi_scale)
                                        if sbw * sbh < (bw * bh * 0.92): 
                                            valid_boxes.append((bx + sbx, by + sby, min(bw, sbw), min(bh, sbh)))
                                            continue
                            valid_boxes.append((bx, by, bw, bh))
                            
                    if not valid_boxes: valid_boxes.append((int(w_high*0.25), int(h_high*0.25), int(w_high*0.5), int(w_high*0.5)))
                    
                    # 👑 👑 👑 【100% 純原圖自適應 ── 最大化物理邊界卡位演算法】 👑 👑 👑
                    # 在高畫質原圖上進行絕對卡位，不外擴不生虛假背景
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
                        
                        # 存檔前最後一秒，反向旋轉還原
                        if is_rotated_for_calculation:
                            cropped = cv2.rotate(cropped, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        
                        # 容量限制二分搜尋法
                        t_bytes = t_mb * 1024 * 1024; low, high, best_q = 1, 100, 85
                        for _ in range(10):
                            mid = (low + high) // 2
                            _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, mid])
                            if len(buf) <= t_bytes: best_q = mid; low = mid + 1
                            else: high = mid - 1
                        _, buf = cv2.imencode(".jpg", cropped, [cv2.IMWRITE_JPEG_QUALITY, best_q])
                        
                        # 寫入雲端打包壓縮包
                        base_name, _ = os.path.splitext(file.name)
                        out_img_name = f"{base_name}_{part_idx}.jpg" if len(valid_boxes) > 1 else f"{base_name}.jpg"
                        zip_file.writestr(out_img_name, buf.tobytes())
                        saved += 1
                except Exception as e:
                    st.error(f"處理失敗 {file.name}: {str(e)}")
                
                progress_bar.progress(idx / len(uploaded_files))
        
        status_text.markdown(f"### ✅ 雲端完美解算成功！共生成 {saved} 張完美的置中原圖！")
        
        # 👑 網頁端一鍵下載 ZIP 打包壓縮檔
        zip_buffer.seek(0)
        st.download_button(
            label="🎁 點擊一鍵下載完美置中相片壓縮包 (ZIP)",
            data=zip_buffer,
            file_name="網拍完美置中裁切成果.zip",
            mime="application/zip"
        )
