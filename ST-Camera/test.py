import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import cv2
import numpy as np
from datetime import datetime

# 设置页面标题
st.title("Streamlit 无 SSL 拍照工具")

# 存储拍照结果（用 session_state 保存，避免刷新丢失）
if "captured_img" not in st.session_state:
    st.session_state.captured_img = None

# 定义拍照回调函数（获取视频帧并保存）
def callback(frame):
    # 转换帧格式（streamlit-webrtc 返回的是 RGB 格式，cv2 是 BGR，需转换）
    img = frame.to_ndarray(format="bgr24")
    return frame  # 实时预览用

# 启动摄像头流（关键：WebRtcMode.LOCAL 模式无需服务器转发，纯本地/内网调用）
webrtc_ctx = webrtc_streamer(
    key="camera",
    mode=WebRtcMode.SENDRECV,  # 本地模式：摄像头数据不经过服务器，仅浏览器本地处理
    rtc_configuration={  # 禁用 SSL 相关配置，强制 HTTP 调用
        "iceServers": [],  # 不使用 ICE 服务器（避免触发 HTTPS 要求）
    },
    video_frame_callback=callback,
    media_stream_constraints={
        "video": True,  # 启用视频（摄像头）
        "audio": False,  # 禁用音频（可选）
    },
    async_processing=True,
)

# 拍照按钮（当摄像头启动后显示）
if webrtc_ctx.state.playing:
    col1, col2, col3 = st.columns(3)
    with col2:
        capture_btn = st.button("📷 拍照")

    # 点击拍照：获取当前视频帧并保存
    if capture_btn and webrtc_ctx.video_frame:
        # 获取当前帧并转换格式（RGB 用于 Streamlit 显示）
        frame = webrtc_ctx.video_frame.to_ndarray(format="rgb24")
        st.session_state.captured_img = frame

        # 保存照片到本地（可选，路径可自定义）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"captured_photo_{timestamp}.jpg"
        # 转换为 BGR 格式保存（cv2 默认格式）
        cv2.imwrite(save_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        st.success(f"照片已保存到：{save_path}")

# 显示拍摄的照片（如果已拍摄）
if st.session_state.captured_img is not None:
    st.subheader("拍摄结果")
    st.image(st.session_state.captured_img, caption="已拍摄照片", use_column_width=True)

    # 二次操作：下载照片（可选）
    is_success, encoded_img = cv2.imencode(".jpg", cv2.cvtColor(st.session_state.captured_img, cv2.COLOR_RGB2BGR))
    if is_success:
        st.download_button(
            label="📥 下载照片",
            data=encoded_img.tobytes(),
            file_name=f"streamlit_photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            mime="image/jpeg",
        )