import io
import os
import sys
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw
import streamlit as st
st.set_page_config(layout="wide")



def is_running_in_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx  # type: ignore
        return get_script_run_ctx() is not None
    except Exception:
        return False


def load_image(file) -> tuple[Image.Image, np.ndarray]:
    image = Image.open(file).convert("RGB")
    np_img = np.array(image)
    return image, np_img


def get_face_cascade() -> cv2.CascadeClassifier:
    cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    return cv2.CascadeClassifier(cascade_path)


def detect_faces(np_img: np.ndarray, scale_factor: float = 1.1, min_neighbors: int = 5, min_size: int = 30):
    gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    cascade = get_face_cascade()
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=scale_factor,
        minNeighbors=min_neighbors,
        minSize=(min_size, min_size),
    )
    return list(map(lambda b: (int(b[0]), int(b[1]), int(b[2]), int(b[3])), faces))


def draw_boxes(pil_img: Image.Image, boxes: list[tuple[int, int, int, int]], color=(255, 0, 0)) -> Image.Image:
    draw = ImageDraw.Draw(pil_img)
    for i, (x, y, w, h) in enumerate(boxes):
        draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
        label_y = y - 12 if y - 12 > 0 else y + 2
        draw.text((x, label_y), f"{i + 1}", fill=color)
    return pil_img


def overlay_rect(pil_img: Image.Image, rect: tuple[int, int, int, int], color=(0, 255, 0)) -> Image.Image:
    draw = ImageDraw.Draw(pil_img)
    x, y, w, h = rect
    draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
    return pil_img


def clamp_rect(x: int, y: int, w: int, h: int, W: int, H: int) -> tuple[int, int, int, int]:
    x = max(0, min(x, W - 1))
    y = max(0, min(y, H - 1))
    w = max(1, min(w, W - x))
    h = max(1, min(h, H - y))
    return int(x), int(y), int(w), int(h)


def crop(np_img: np.ndarray, rect: tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = rect
    return np_img[y : y + h, x : x + w]


def to_jpg_bytes(np_img: np.ndarray, quality: int = 95) -> bytes:
    im = Image.fromarray(np_img).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def run_app():
    import streamlit as st



    st.set_page_config(page_title="人脸截图编辑器", page_icon="🖼️", layout="wide")
    st.title("人脸截图编辑器")

    # 历史持久化目录（跨会话保存）
    history_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history")
    try:
        os.makedirs(history_dir, exist_ok=True)
    except Exception:
        pass

    st.set_page_config(layout="wide")
    uploaded = st.file_uploader("---", type=["jpg", "jpeg", "png", "webp", "bmp"])
    st.set_page_config(layout="wide")
    if uploaded is None:
        st.info("请先上传一张图片，或查看下方的上次结果。")
        # 无上传时展示历史结果（四栏）
        st.markdown("---")
        st.subheader("历史结果")
        last_detection_bytes = st.session_state.get("last_detection_bytes")
        last_edited_bytes = st.session_state.get("last_edited_bytes")
        last_ai_bytes = st.session_state.get("last_ai_bytes")

        # 从本地读取持久化的历史（作为回退）
        if not last_detection_bytes:
            det_path = os.path.join(history_dir, "last_detection.jpg")
            if os.path.exists(det_path):
                try:
                    with open(det_path, "rb") as f:
                        last_detection_bytes = f.read()
                        st.session_state.last_detection_bytes = last_detection_bytes
                except Exception:
                    pass
        if not last_edited_bytes:
            edited_path = os.path.join(history_dir, "last_edited.jpg")
            if os.path.exists(edited_path):
                try:
                    with open(edited_path, "rb") as f:
                        last_edited_bytes = f.read()
                        st.session_state.last_edited_bytes = last_edited_bytes
                except Exception:
                    pass
        if not last_ai_bytes:
            ai_path = os.path.join(history_dir, "last_ai.jpg")
            if os.path.exists(ai_path):
                try:
                    with open(ai_path, "rb") as f:
                        last_ai_bytes = f.read()
                        st.session_state.last_ai_bytes = last_ai_bytes
                except Exception:
                    pass

        c1, c2, c3, c4 = st.columns(4)
        with c1:

            if last_detection_bytes:
                try:
                    img_last_det = Image.open(io.BytesIO(last_detection_bytes))
                    with st.container(height=600):
                        st.image(img_last_det, caption="上次检测结果（OpenCV）", use_container_width=True)
                except Exception:
                    st.warning("无法渲染上次检测结果预览")
                st.download_button("下载上次检测结果 (JPG)", data=last_detection_bytes, file_name="last_detection.jpg", mime="image/jpeg", use_container_width=True)
            else:
                st.info("暂无上次检测结果")

        with c2:
            if last_edited_bytes:
                try:
                    img_last_edited = Image.open(io.BytesIO(last_edited_bytes))
                    with st.container(height=600):
                        st.image(img_last_edited, caption="上次二次编辑预览", use_container_width=True)
                except Exception:
                    st.warning("无法渲染上次二次编辑预览")
                st.download_button("下载上次二次编辑 (JPG)", data=last_edited_bytes, file_name="last_face_edited.jpg", mime="image/jpeg", use_container_width=True)
            else:
                st.info("暂无上次二次编辑结果")

        with c3:
            if last_ai_bytes:
                try:
                    img_last_ai = Image.open(io.BytesIO(last_ai_bytes))
                    with st.container(height=600):
                        st.image(img_last_ai, caption="上次 AI 剪裁预览", use_container_width=True)
                except Exception:
                    st.warning("无法渲染上次 AI 剪裁预览")
                st.download_button("下载上次 AI 剪裁 (JPG)", data=last_ai_bytes, file_name="last_face_ai.jpg", mime="image/jpeg", use_container_width=True)
            else:
                st.info("暂无上次 AI 剪裁结果")
        with c4:
            st.caption("预留列 4")
        return

    pil_img, np_img = load_image(uploaded)
    H, W = np_img.shape[:2]
    st.set_page_config(layout="wide")
    # 读取或初始化检测参数（控件在下方编辑组中，值存于 session_state）
    cfg_sf = st.session_state.get("cfg_sf", 1.10)
    cfg_mn = st.session_state.get("cfg_mn", 5)
    cfg_ms = st.session_state.get("cfg_ms", 30)

    # 根据当前参数进行人脸检测
    faces = detect_faces(np_img, cfg_sf, cfg_mn, cfg_ms)
    labeled_img = draw_boxes(pil_img.copy(), faces)

    # 初始化选择与裁剪框
    if "last_face_index" not in st.session_state:
        st.session_state.last_face_index = 0
    if "rect" not in st.session_state:
        if len(faces) > 0:
            st.session_state.rect = tuple(map(int, faces[st.session_state.last_face_index]))
        else:
            st.session_state.rect = (W // 4, H // 4, W // 2, H // 2)

    st.set_page_config(layout="wide")
    # 当前裁剪框（用于上方展示组）
    x0, y0, w0, h0 = clamp_rect(*st.session_state.rect, W, H)
    rect_current = (x0, y0, w0, h0)
    crop_img_current = crop(np_img, rect_current)
    orig_crop = crop(np_img, tuple(map(int, faces[st.session_state.last_face_index]))) if len(faces) > 0 else None
    st.set_page_config(layout="wide")
    # 分栏组 1：检测结果、裁剪预览、下载 AI 剪裁结果
    st.markdown("---")
    st.set_page_config(layout="wide")
    st.subheader("检测结果与预览")
    st.set_page_config(layout="wide")
    g1_left, g1_middle, g1_right = st.columns([1, 1, 1])
    with g1_left:
        with st.container(height=600):
            st.image(labeled_img, caption=f"检测到 {len(faces)} 张人脸", use_container_width=True)
    with g1_middle:
        with st.container(height=600):
            st.image(crop_img_current, caption="裁剪预览", use_container_width=True)
    with g1_right:
        if orig_crop is not None:
            st.download_button(
                "下载AI剪裁结果 (JPG)",
                data=to_jpg_bytes(orig_crop),
                file_name="face_ai.jpg",
                mime="image/jpeg",use_container_width=True
            )
        else:
            st.button("下载AI剪裁结果 (JPG)", disabled=True)

    # 分栏组 2：二次编辑（检测参数、人脸选择、裁剪框滑块、缩略图、下载调整后）
    st.markdown("---")
    st.set_page_config(layout="wide")
    st.subheader("二次编辑")
    g2_left, g2_middle, g2_right, g2_right2  = st.columns([1, 1, 1, 1])
    st.set_page_config(layout="wide")

    with g2_left:
        with st.container(height=600):
            with st.expander("人脸检测参数", expanded=True):
                cfg_sf_new = st.slider("检测尺度 scaleFactor", 1.05, 1.50, cfg_sf, 0.01)
                cfg_mn_new = st.slider("最小邻居数 minNeighbors", 1, 10, cfg_mn, 1)
                cfg_ms_new = st.slider("最小人脸尺寸（像素）", 20, 200, cfg_ms, 2)
            # 更新参数到会话，供下一次刷新检测使用
            st.session_state.cfg_sf = cfg_sf_new
            st.session_state.cfg_mn = cfg_mn_new
            st.session_state.cfg_ms = cfg_ms_new
    with g2_middle:
        with st.container(height=600):
            # 人脸选择与重置
            if len(faces) == 0:
                st.warning("未检测到人脸，可手动选择裁剪区域。")
            else:
                idx = st.selectbox(
                    "选择要裁剪的人脸",
                    options=list(range(len(faces))),
                    index=min(st.session_state.last_face_index, len(faces) - 1),
                    format_func=lambda i: f"人脸 {i + 1}",
                )
                if idx != st.session_state.last_face_index:
                    st.session_state.last_face_index = idx
                    st.session_state.rect = tuple(map(int, faces[idx]))
            st.markdown("---")
            if st.button("重置为检测框"):
                if len(faces) > 0:
                    st.session_state.rect = tuple(map(int, faces[st.session_state.last_face_index]))
                else:
                    st.session_state.rect = (W // 4, H // 4, W // 2, H // 2)

            # 读取当前裁剪框并提供滑块编辑
            x, y, w, h = clamp_rect(*st.session_state.rect, W, H)
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                x = st.slider("X", 0, W - 1, x, 1)
                y = st.slider("Y", 0, H - 1, y, 1)
            with s_col2:
                w = st.slider("宽度 W", 1, W, w, 1)
                h = st.slider("高度 H", 1, H, h, 1)

            x, y, w, h = clamp_rect(x, y, w, h, W, H)
            st.session_state.rect = (x, y, w, h)
            st.write("当前裁剪框：", (x, y, w, h))
    st.set_page_config(layout="wide")
    with g2_right:
        with st.container(height=600):
            # 缩略图与下载调整后的裁剪图
            thumb_overlay = overlay_rect(pil_img.copy(), (x, y, w, h))
            st.image(thumb_overlay, caption="原图缩略图（含裁剪框）")
            crop_img = crop(np_img, (x, y, w, h))
    with g2_right2:
        with st.container(height=600):
            st.image(crop_img, caption="裁剪区缩略图")
            adj_bytes = to_jpg_bytes(crop_img)
    
    st.download_button("下载调整后裁剪图 (JPG)", data=adj_bytes, file_name="face_edited.jpg", mime="image/jpeg",use_container_width=True)

    # 底部分栏组（四栏）：展示上次结果与下载按钮
    st.markdown("---")
    st.subheader("历史结果")
    last_detection_bytes = st.session_state.get("last_detection_bytes")
    last_edited_bytes = st.session_state.get("last_edited_bytes")
    last_ai_bytes = st.session_state.get("last_ai_bytes")

    with st.container(height=600):
        c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.caption("预留列 1")

    with c2:
        if last_edited_bytes:
            try:
                img_last_edited = Image.open(io.BytesIO(last_edited_bytes))
                with st.container(height=600):
                    st.image(img_last_edited, caption="上次二次编辑预览", use_container_width=True)
            except Exception:
                st.warning("无法渲染上次二次编辑预览")
            st.download_button("下载上次二次编辑 (JPG)", data=last_edited_bytes, file_name="last_face_edited.jpg", mime="image/jpeg", use_container_width=True)
        else:
            st.info("暂无上次二次编辑结果")

    with c3:
        with st.container(height=600):
            if last_ai_bytes:
                try:
                    img_last_ai = Image.open(io.BytesIO(last_ai_bytes))
                    with st.container(height=600):
                        st.image(img_last_ai, caption="上次 AI 剪裁预览", use_container_width=True)
                except Exception:
                    st.warning("无法渲染上次 AI 剪裁预览")
                st.download_button("下载上次 AI 剪裁 (JPG)", data=last_ai_bytes, file_name="last_face_ai.jpg", mime="image/jpeg", use_container_width=True)
            else:
                st.info("暂无上次 AI 剪裁结果")
    with c4:
        st.caption("预留列 4")

    # 在界面渲染完成后，更新“上次结果”为当前结果（OpenCV 检测图 + 二次编辑 + AI 剪裁）
    det_bytes = to_jpg_bytes(np.array(labeled_img))
    st.session_state.last_detection_bytes = det_bytes
    curr_ai_bytes = to_jpg_bytes(orig_crop) if orig_crop is not None else None
    st.session_state.last_ai_bytes = curr_ai_bytes
    st.session_state.last_edited_bytes = adj_bytes

    # 同步持久化到本地，便于跨会话保存
    try:
        if det_bytes:
            with open(os.path.join(history_dir, "last_detection.jpg"), "wb") as f:
                f.write(det_bytes)
        if curr_ai_bytes:
            with open(os.path.join(history_dir, "last_ai.jpg"), "wb") as f:
                f.write(curr_ai_bytes)
        if adj_bytes:
            with open(os.path.join(history_dir, "last_edited.jpg"), "wb") as f:
                f.write(adj_bytes)
    except Exception:
        pass


if __name__ == "__main__":
    if is_running_in_streamlit():
        run_app()
    else:
        cmd = [sys.executable, "-m", "streamlit", "run", os.path.abspath(__file__), "--server.headless", "true"]
        subprocess.run(cmd, check=False)