import streamlit as st
import streamlit_extras
from fc_container import *

# ---------------------- 基础函数 ----------------------
from fc_base import *

fc_head()

# ---------------------- 关键：设置宽屏模式 ----------------------
st.set_page_config(
    page_title="DPTK-Frontend",
    layout="wide",  # 核心配置：启用宽屏模式
    page_icon="📊"
)


# ---------------------- 创建 Tab 容器 ----------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7,tab8 = st.tabs(["📊 介绍", "🔧 OA-2025", "🖼️ OA-2025-说明书","OA-2025-工作日志","OA-2019","SCTZ-云盘","Leyon-云盘","Error-Cards"])

# ---------------------- 填充 Tab 内容 ----------------------
with tab1:fc_container_1()
with tab2:fc_container_2()
with tab3:fc_container_3()
with tab4:fc_container_4()
with tab5:fc_container_6()
with tab6:fc_container_6()
with tab7:fc_container_7()
with tab8:fc_container_8()

