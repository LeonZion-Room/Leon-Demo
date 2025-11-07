import streamlit as st
from page_fc import *

if "dt" not in st.session_state:
    st.session_state.dt = {}
    # 设置全宽
    st.set_page_config(layout="wide")

# 设置多级标签页
tab0,tab1,tab2,tab3= st.tabs(["介绍", "入口","更新记录","使用说明"])

# 设置介绍部分
with tab0:
    page_front()
# 设置入口部分
with tab1:
    page_entry()
# 设置更新记录部分
with tab2:
    page_update()
# 设置使用说明部分
with tab3:
    page_usage()



