import os
from io import BytesIO
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
import streamlit as st
import av
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode


st.set_page_config(page_title="ST Camera", layout="wide")
st.title("拍照系统 (Streamlit + 第三方组件)")
st.caption("使用 Streamlit 的摄像头组件进行抓拍，同时集成 streamlit-webrtc 进行实时预览与人脸检测。")


# Sidebar 配置与目录准备
captures_dir = st.sidebar.text_input("原图保存目录", value="captures")
faces_dir = st.sidebar.text_input("人脸保存目录", value="faces")
os.makedirs(captures_dir, exist_ok=True)
os.makedirs(faces_dir, exist_ok=True)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


def pil_to_jpg_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def detect_and_crop_faces(img: Image.Image):
    bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(60, 60))
    crops = []
    for (x, y, w, h) in faces:
        crop = img.crop((x, y, x + w, y + h))
        crops.append(((x, y, w, h), crop))
    return crops


def draw_faces(img: Image.Image, boxes):
    bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    for (x, y, w, h) in boxes:
        cv2.rectangle(bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


tab1, tab2 = st.tabs(["拍照并下载", "实时预览（第三方组件）"])


with tab1:
    st.subheader("使用内置摄像头进行抓拍")
    img_file = st.camera_input("点击下方按钮拍照")
    if img_file is not None:
        img = Image.open(img_file)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"capture_{ts}.jpg"
        save_path = os.path.join(captures_dir, base_name)
        img_bytes = pil_to_jpg_bytes(img)

        # 保存原图
        with open(save_path, "wb") as f:
            f.write(img_bytes)
        st.success(f"已保存原图到: {save_path}")

        st.image(img, caption="原图预览", use_column_width=True)
        st.download_button("下载原图 JPG", data=img_bytes, file_name=base_name, mime="image/jpeg")

        # 人脸检测与裁剪
        crops = detect_and_crop_faces(img)
        st.write(f"识别到 {len(crops)} 张人脸")
        if len(crops) > 0:
            boxes = [c[0] for c in crops]
            st.image(draw_faces(img, boxes), caption="人脸框预览", use_column_width=True)

            for idx, ((x, y, w, h), face_img) in enumerate(crops, start=1):
                face_name = f"face_{ts}_{idx}.jpg"
                face_path = os.path.join(faces_dir, face_name)
                face_bytes = pil_to_jpg_bytes(face_img)
                with open(face_path, "wb") as f:
                    f.write(face_bytes)
                st.download_button(
                    f"下载人脸 {idx} JPG",
                    data=face_bytes,
                    file_name=face_name,
                    mime="image/jpeg",
                )
        else:
            st.info("未检测到人脸，请调整光线或角度后重试。")


class FaceOverlayProcessor(VideoProcessorBase):
    def __init__(self):
        self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(60, 60))
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return av.VideoFrame.from_ndarray(img, format="bgr24")


with tab2:
    st.subheader("基于 streamlit-webrtc 的实时摄像头预览")
    st.caption("实时检测并叠加人脸框，抓拍与下载请在“拍照并下载”页进行。")
    webrtc_streamer(
        key="camera",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=FaceOverlayProcessor,
        media_stream_constraints={"video": True, "audio": False},
    )