import streamlit as st
import base64


# markdown 渲染
def render_markdown(text):
    st.markdown(text, unsafe_allow_html=True)

# pdf 展示
# - 不要边框 | 居中展示 | 全宽适应屏幕
def show_pdf(file_path):
    with open(file_path, "rb") as f:base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # 居中展示 | 全宽适应屏幕
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf" style="border: none; display: block; margin: 0 auto;">'
    # 居中展示
    st.markdown(pdf_display, unsafe_allow_html=True)

# 图片展示
# - 居中展示 | 全宽适应屏幕
def show_image(file_path):
    # 居中展示
    st.image(file_path, caption=None, use_column_width="auto", clamp=False, channels="RGB", output_format="auto")

# 脚注
def show_footer():
    cols = st.columns(3)
    with cols[1]:
        st.markdown("---")
        

def create_transparent_border_card(logo_url: str, link: str, name: str, desc: str, border_color: str = "rgba(120,120,120,0.2)", border_radius: str = "8px"):
    """
    生成透明带边框的卡片组件，布局为左侧图标+右侧文字（名称+描述）
    
    参数:
    logo_url: Logo图片的URL地址（支持网络图片或本地路径）
    link: 点击卡片跳转的目标链接（http/https开头）
    name: 卡片显示的名称
    desc: 卡片的描述文字
    border_color: 边框颜色（默认半透明白色）
    border_radius: 边框圆角（默认8px）
    """
    # 处理本地Logo路径
    if logo_url.startswith(("http://", "https://")):
        img_src = logo_url
    else:
        from PIL import Image
        import io
        import base64
        try:
            with Image.open(logo_url) as img:
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                img_src = f"data:image/png;base64,{img_base64}"
        except Exception as e:
            img_src = "https://cdn-icons-png.flaticon.com/512/25/25694.png"
            st.warning(f"本地Logo加载失败，使用默认图标: {str(e)}")
    
    # 卡片HTML模板（透明背景+边框，左右布局）
    card_html = f"""
    <a href="{link}" target="_blank" style="text-decoration: none; display: block;">
        <div style="
            display: flex;
            align-items: center;
            background-color: transparent;
            border: 1px solid {border_color};
            border-radius: {border_radius};
            padding: 8px 12px;
            margin: 8px 0;
            transition: all 0.3s ease;
        ">
            <div style="
                width: 40px;
                height: 40px;
                border-radius: 4px;
                overflow: hidden;
                margin-right: 12px;
            ">
                <img src="{img_src}" alt="{name} Logo" style="
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                " onError="this.src='https://cdn-icons-png.flaticon.com/512/25/25694.png';">
            </div>
            <div style="
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <span style="
                    font-size: 16px;
                    font-weight: 600;
                    color: rgba(0,0,0,0.7);
                ">{name}</span>
                <span style="
                    font-size: 12px;
                    color: rgba(0,0,0,0.7);
                ">{desc}</span>
            </div>
        </div>
    </a>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)