import streamlit as st
from module_fc import *
import os
import time



def page_front():
    # 居中文本
    st.markdown("<h1 style='text-align: center;'>Welcome to DPTK-NAS</h1>", unsafe_allow_html=True)
    # 设置布局
    st.markdown("<br>", unsafe_allow_html=True)
    col0,col1 = st.columns([1,4])
    # 内容
    mdsh0 = "#### 项目介绍"
    mds0 = """
    - 本项目基于 FN 进行实现
    - 后续出于安全考虑，将基于公司等保测评相关安全服务器进行流量转发，以实现对公网访问的安全保护
    - 现部署于大鹏投控运营管理部处机群，文件相关二次保护服务已于机群中进行实现
    - 电脑端请基于网页进行访问，移动端请基于 APP 进行访问，相关软件下载链接详见本网页资料处
    """
    mdsh1 = "#### 项目使用说明"
    mds1 = """
    - 请在公司网络环境下访问公司内部网站，不在公司网络环境下请访问公司外部网站，详见本网页入口处说明
    - 公司内部访问速度预计20M/S | 公司外部访问速度预计3M/S
    - 权限分配请联系 phone:19580783095
    """
    # 渲染
    with col0:
        st.image("a.png", caption=None, use_container_width=True, clamp=False, channels="RGB", output_format="auto")
    with col1:
        st.info(mdsh0)
        render_markdown(mds0)
        st.success(mdsh1)
        render_markdown(mds1)

def page_entry():
    # 居中文本
    st.markdown("<h1 style='text-align: center;'>Into</h1>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    # 布局
    col0,col1 = st.columns([1,1])
    with col0:
        # 内容
        mds = """
        - 在公司wifi下或有线连接公司网络，称为内网环境
        - 公司网络环境下请点击以下卡片进入云盘
        """
        st.error("### 内网环境")
        render_markdown(mds)
        # 展示卡片
        create_transparent_border_card(logo_url="http://8.138.240.134:13002/uploads/2025/10/23/073c9c4ef1c0ed0edff406cbf024274b.ico", link="http://172.168.12.142:5667/", name="DPTK-NAS", desc="NAS-内网入口")

    with col1:
        # 内容
        mds = """
        - 不在公司网络环境下，称为外网环境
        - 非公司网络环境下请点击以下卡片进入云盘
        """
        st.warning("### 外网环境")
        render_markdown(mds)
        # 展示卡片
        create_transparent_border_card(logo_url="http://8.138.240.134:13002/uploads/2025/10/23/073c9c4ef1c0ed0edff406cbf024274b.ico", link="http://119.145.17.34:5667/", name="DPTK-NAS", desc="NAS-外网入口")


def page_update():
    # 按照顺序读取目录文件
    path = "mds"
    files = os.listdir(path)
    # 从最新排到最老
    files.sort(reverse=True)
    # 展示文件内容
    for file in files:
        # 拼接文件路径
        file_path = os.path.join(path, file)
        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 展示文件创建时间-中文格式
        st.write(f"> ##### 更新日期: {time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getctime(file_path)))})"[:-1])
        # 展示文件内容
        st.markdown(content)
        # 分割栏
        st.markdown("---")

def page_usage():
    cols = st.columns([4,1])
    with cols[0]:
        # 居中文本
        st.markdown("<h1 style='text-align: center;'>使用说明</h1>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        # PDF
        show_pdf("files/a.pdf")
    with cols[1]:
        # 资料下载-url
        st.markdown("> #### APK-下载链接")
        create_transparent_border_card(logo_url="http://8.138.240.134:13002/uploads/2025/10/23/073c9c4ef1c0ed0edff406cbf024274b.ico", link="https://fnos.net/dptk-fnos/", name="DPTK-NAS", desc="基于FNOS的云盘服务")
        # 其它说明
        st.markdown("""
        ---
        - 可鼠标直接在制定区域缩放 pdf 进行查看
        - 可直接下载 pdf 进行查看
        - 手机端登录部分，相关说明位于说明书尾部
        """)

def page_download():
    # 居中文本
    st.markdown("<h1 style='text-align: center;'>Download</h1>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
