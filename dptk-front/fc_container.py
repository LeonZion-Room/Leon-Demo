import streamlit as st
import streamlit_extras
from fc_base import *



def fc_container_1():
    # ---------------------- 标题 ----------------------
    st.title("介绍")
    # ---------------------- 内容 ----------------------
    st.code("""
- 本网站用于记录投控公司相关网络与信息服务的登入端口
- 为便于查询与避免重复输入网页链接，已将链接与标签基于网页卡片形式进行展示
- 相关敏感信息已去除,用户密码等信息请参考通知
- 主要包含：0A-2025-入口 | OA-2025-入口链接 | OA-2019-入口 | SCTZ-NAS | Leyon-NAS | Error-Cards
""",language="markdown")
    # ---------------------- 页脚 ----------------------
    fc_foot()


def fc_container_2():
    # ---------------------- 标题 ----------------------
    st.title("OA-2025")

    # ---------------------- 内容 ----------------------
    st.code("""
- 此项目为 25年7月启动开发的投控OA系统，用于管理投控公司相关流程与各类必要日常服务
- 服务器部署于 大鹏新区-生命科学产业园-政数局-B1机房
- 现处于试运行阶段,现将相关安排公告如下：
    1. 新系统上线初期实行新旧系统并行运行，大家可通过新系统进行数据测试操作。
    2. 测试期间，业务审核仍以旧系统流程为准，请务必严格遵照执行。
    3. 请大家在测试过程中及时记录遇到的使用问题，综合办将于本周五组织专项培训会，集中解答相关疑问。
    4. 下周一起，新系统正式启用，后续将逐步完成新旧系统切换并进行必要配置。
- 请各位同事积极参与测试与培训，确保新系统顺利落地运行。如有紧急问题，可随时联系综合办沟通。""",language="markdown")

    st.divider()

    # 卡片与入口
    cols = st.columns(3)
    with cols[0]:
        st.info("##### 公司网络环境-入口")
        zyoa_img = "https://ts2.tc.mm.bing.net/th/id/OIP-C.SGvcMipdtXRb2Dd-a7wXxgHaFj?rs=1&pid=ImgDetMain&o=7&rm=3"
        zyoa_url = "http://119.145.17.34:8012/seeyon/index.jsp"
        fc_card(title="0A-2025-入口",text="新版预上线OA | 公司内网环境 | 访问速度更快",image=zyoa_img,url=zyoa_url)
    with cols[1]:
        st.info("##### 非公司网络环境-入口")
        zyoa_img = "https://ts2.tc.mm.bing.net/th/id/OIP-C.SGvcMipdtXRb2Dd-a7wXxgHaFj?rs=1&pid=ImgDetMain&o=7&rm=3"
        zyoa_url = "http://172.168.10.97:8012/seeyon/index.jsp"
        fc_card(title="0A-2025-入口",text="新版预上线OA | 外网环境 | 访问更灵活",image=zyoa_img,url=zyoa_url)
    with cols[2]:
        st.warning("##### OA-2025开发环境入口")
        zyoa_img = "https://ts2.tc.mm.bing.net/th/id/OIP-C.SGvcMipdtXRb2Dd-a7wXxgHaFj?rs=1&pid=ImgDetMain&o=7&rm=3"
        zyoa_url = "http://218.18.233.27:8012"
        fc_card(title="OA-2025-开发环境",text="用于开发 | 实时跟进新需求与开发 | 确定后将合并入正式环境",image=zyoa_img,url=zyoa_url)


    # ---------------------- 页脚 ----------------------
    fc_foot()

def fc_container_3():
    # ---------------------- 标题 ----------------------
    st.title("OA-2025-入口链接说明书")


    # ---------------------- 入口链接 ----------------------
    st.write("""
    - 此部分内容用于陈列各功能模块的使用入口链接
    - 由于 PDF 展示视频相对不方便，因此通过 在线版说明书 实现演示视频的展示
    - 同时提供pdf下载与必要的演示视频用于介绍与入口链接
    - 点击卡片可跳转至对应页面进行入口链接的内容查看
    - 通过附件区可直接下载对应的入口链接 .pdf 文件
    """)
    st.divider()
    # ---------------------- 内容 ----------------------
    cols = st.columns(3)
    with cols[0]:
        st.info("##### 入口链接书文档在线查看")
        demo_slides = [
            {"image": "http://119.145.17.34:40061/i/2025/11/18/g86ld.png",
             "title": "项目介绍",
             "text": "基于致远系统云实现 | 新版预上线OA",
             "url": "https://bzfzgndbrg.feishu.cn/wiki/DmcBwTtkai3GHokyoIYcWf0Xnrc?from=from_copylink"},
             {"image": "http://119.145.17.34:40061/i/2025/11/18/g89aa.png",
             "title": "说明书-日常审批",
             "text": "该模块涵盖员工请假单、公务车辆使用申请表（用车申请类）、出差审批表、员工缺勤情况说明、办公用品（固资）事前呈批单、发文呈批表、议题申请表及通用呈批表等核心表单。",
             "url": "https://bzfzgndbrg.feishu.cn/wiki/XY82wRKYdiNp4pknDWtcQiRrnih"},
             {"image": "http://119.145.17.34:40061/i/2025/11/18/g87d8.png",
             "title": "说明书-督办模块",
             "text": "该模块主要用于项目管理、任务分配与进度监控，确保项目按计划进行。",
             "url": "https://bzfzgndbrg.feishu.cn/wiki/O1jBwS4zti7n7VkAiXMcb1TtnFd"},
             {"image": "http://119.145.17.34:40061/i/2025/11/18/g83ec.png",
             "title": "说明书-费用模块",
             "text": "与财管中心对接调整中 ...",
             "url": "https://bzfzgndbrg.feishu.cn/wiki/LDiKwlh0HiMZqzk0teUcO8L3nah"},
             {"image": "http://119.145.17.34:40061/i/2025/11/18/g88bo.png",
             "title": "说明书-招采模块",
             "text": "该模块主要用于采购需求的提交、审批、管理，确保采购活动按计划进行。",
             "url": "https://bzfzgndbrg.feishu.cn/wiki/GdsywghPXimZQbkCELmctzoVnab"},
             {"image": "http://119.145.17.34:40061/i/2025/11/18/g87yu.png",
             "title": "说明书-预算模块",
             "text": "该模块主要用于预算与费用控制界限计划。",
             "url": "https://bzfzgndbrg.feishu.cn/wiki/DZvUww2VGiBY1VklyluczB2Vnug"},
             {"image": "http://119.145.17.34:40061/i/2025/11/18/g87k1.png",
             "title": "说明书-法务模块",
             "text": "该模块主要用于公司内部法务咨询等功能 ...",
             "url": "https://bzfzgndbrg.feishu.cn/wiki/QDMxwyJZ6i4ewtkfILXcFUdEn0c"}]
        fc_carousel(slides=demo_slides, height=400, sec_per_slide=3, max_width=None,full_viewport=False)


    with cols[1]:
        st.warning("##### 说明书-pdf-下载")
        table_data = [
            {"文件名称": "0A-2025-首页", "下载链接": ""},
            {"文件名称": "0A-2025-日常审批", "下载链接": "新版预上线OA | 公司内网环境 | 访问速度更快"},
            {"文件名称": "0A-2025-督办模块", "下载链接": "新版预上线OA | 公司内网环境 | 访问速度更快"},
            {"文件名称": "0A-2025-法务模块", "下载链接": "新版预上线OA | 公司内网环境 | 访问速度更快"},
            {"文件名称": "0A-2025-招采模块", "下载链接": "新版预上线OA | 公司内网环境 | 访问速度更快"},
            {"文件名称": "0A-2025-预算模块", "下载链接": "新版预上线OA | 公司内网环境 | 访问速度更快"},
            {"文件名称": "0A-2025-费用模块", "下载链接": "新版预上线OA | 公司内网环境 | 访问速度更快"},
        ]
        st.table(table_data)

    with cols[2]:
        st.success("##### 说明书-视频演示")
        tabs = st.tabs(["日常审批", "督办模块", "法务模块", "招采模块", "预算模块", "费用模块"]) 
        with tabs[0]:
            _u = "http://119.145.17.34:8001/stream/compressed/23fda320-bfeb-44f1-9cb1-bc54294f1eae"
            if _u.endswith(".m3u8") or "m3u8" in _u:
                fc_hls_player(_u, height=360, muted=True, autoplay=True, controls=True)
            else:
                st.video(_u)

            if st.button("大屏播放", key="vid0",use_container_width=True):
                    st.session_state["video_modal_open"] = True
                    st.session_state["video_modal_url"] = _u
                    st.session_state["video_modal_title"] = "日常审批"
        with tabs[1]:
            _u = "http://119.145.17.34:8001/stream/compressed/57059362-22d8-45d1-a558-d851c484e830"
            if _u.endswith(".m3u8") or "m3u8" in _u:
                fc_hls_player(_u, height=360, muted=True, autoplay=True, controls=True)
            else:
                st.video(_u)

            if st.button("大屏播放", key="vid1",use_container_width=True):
                    st.session_state["video_modal_open"] = True
                    st.session_state["video_modal_url"] = _u
                    st.session_state["video_modal_title"] = "督办模块"
        with tabs[2]:
            _u = "http://119.145.17.34:8001/stream/compressed/d6f9b116-e13e-461d-a517-de9a7284cdbf"
            if _u.endswith(".m3u8") or "m3u8" in _u:
                fc_hls_player(_u, height=360, muted=True, autoplay=True, controls=True)
            else:
                st.video(_u)
            _c = st.columns([1,1,1])
            with _c[1]:
                if st.button("大屏播放", key="vid5",use_container_width=True):
                    st.session_state["video_modal_open"] = True
                    st.session_state["video_modal_url"] = _u
                    st.session_state["video_modal_title"] = "法务模块"
        with tabs[3]:
            _u = "http://119.145.17.34:8001/stream/compressed/feb01396-7197-426f-902a-d9f86d18db90"
            if _u.endswith(".m3u8") or "m3u8" in _u:
                fc_hls_player(_u, height=360, muted=True, autoplay=True, controls=True)
            else:
                st.video(_u)

            if st.button("大屏播放", key="vid3",use_container_width=True):
                    st.session_state["video_modal_open"] = True
                    st.session_state["video_modal_url"] = _u
                    st.session_state["video_modal_title"] = "招采模块"
        with tabs[4]:
            _u = "http://119.145.17.34:8001/stream/compressed/a1df344d-06ff-4a43-bba5-819c4d1d6735"
            if _u.endswith(".m3u8") or "m3u8" in _u:
                fc_hls_player(_u, height=360, muted=True, autoplay=True, controls=True)
            else:
                st.video(_u)

            if st.button("大屏播放", key="vid4",use_container_width=True):
                    st.session_state["video_modal_open"] = True
                    st.session_state["video_modal_url"] = _u
                    st.session_state["video_modal_title"] = "预算模块"
        with tabs[5]:
            _u = "https://ts2.tc.mm.bing.net/th/id/OIP-C.444444444444444444444444?rs=1&pid=ImgDetMain&o=7&rm=3"
            if _u.endswith(".m3u8") or "m3u8" in _u:
                fc_hls_player(_u, height=360, muted=True, autoplay=True, controls=True)
            else:
                st.error("费用模块开发中，与财管中心对接调整中 ...")

            if st.button("大屏播放", key="vid2",use_container_width=True):
                    st.session_state["video_modal_open"] = True
                    st.session_state["video_modal_url"] = _u
                    st.session_state["video_modal_title"] = "费用模块"


        if "video_modal_open" not in st.session_state:
            st.session_state["video_modal_open"] = False
        @st.dialog("视频全屏播放", width="large")
        def _video_modal():
            url = st.session_state.get("video_modal_url", "")
            title = st.session_state.get("video_modal_title", "")
            if title:
                st.subheader(title)
            if url:
                if url.endswith(".m3u8") or "m3u8" in url:
                    fc_hls_player(url, height=600, muted=False, autoplay=True, controls=True)
                else:
                    st.video(url)
        if st.session_state["video_modal_open"]:
            _video_modal()

    # ---------------------- 页脚 ----------------------
    fc_foot()

def fc_container_4():
    st.subheader("开发日志")
    options = ["7月", "8月", "9月", "10月", "11月"]
    selected = st.multiselect("请选择日期月份", options)
    month_prefix = {
        "7月": "7-",
        "8月": "8-",
        "9月": "9-",
        "10月": "10-",
        "11月": "11-",
    }
    import os
    img_dir = os.path.join(os.getcwd(), "logs")
    valid_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    all_images = []
    if os.path.isdir(img_dir):
        for name in os.listdir(img_dir):
            ext = os.path.splitext(name)[1].lower()
            if ext in valid_exts:
                all_images.append(name)
    prefixes = [month_prefix[m] for m in selected if m in month_prefix] if selected else []
    if prefixes:
        show_list = [n for n in all_images if any(n.startswith(p) for p in prefixes)]
    else:
        show_list = all_images
    show_list.sort()
    if 'log_viewer_open' not in st.session_state:
        st.session_state['log_viewer_open'] = False
    if 'log_viewer_index' not in st.session_state:
        st.session_state['log_viewer_index'] = 0
    if not show_list:
        st.info("未找到符合条件的图片")
    else:
        cols = st.columns(4)
        import base64
        mime_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp'}
        payload = []
        for i, fname in enumerate(show_list):
            with cols[i % 4]:
                title = f"{fname[:-4]} 日志"
                with st.expander(title, expanded=True):
                    fpath = os.path.join(img_dir, fname)
                    try:
                        ext = os.path.splitext(fname)[1].lower()
                        mime = mime_map.get(ext, 'image/png')
                        with open(fpath, 'rb') as fh:
                            b64 = base64.b64encode(fh.read()).decode('utf-8')
                        payload.append({'name': fname, 'path': fpath})
                        with st.container(border=True,height=200):
                            st.image(fpath, use_container_width =True)
                        _cols = st.columns([1,1,1])
                        with _cols[1]:
                            if st.button("放大查看", key=f"open_{i}"):
                                st.session_state['log_viewer_open'] = True
                                st.session_state['log_viewer_index'] = i
                    except Exception:
                        st.warning(f"无法打开图片: {fname}")
        @st.dialog("日志查看", width="large")
        def _log_modal():
            if not payload:
                st.write("无图片")
                return
            _i = st.session_state.get('log_viewer_index', 0)
            _i = max(0, min(_i, len(payload)-1))
            _name = payload[_i]['name']
            _path = payload[_i]['path']
            st.success(f"## 当前查看：{_name}")
            st.image(_path, use_container_width =True)
            nav = st.columns(2)
            with nav[0]:
                if st.button("上一张", key="prev_modal",use_container_width=True):
                    st.session_state['log_viewer_index'] = (_i - 1) % len(payload)
            with nav[1]:
                if st.button("下一张", key="next_modal",use_container_width=True):
                    st.session_state['log_viewer_index'] = (_i + 1) % len(payload)
        if st.session_state['log_viewer_open']:
            _log_modal()

    fc_foot()

def fc_container_5():
    # ---------------------- 标题 ----------------------
    st.title("OA-2019")

    cols = st.columns(2)

    # ---------------------- 内容 ----------------------
    with cols[0]:
        st.write("""
        - 2019年建立，泛微OA系统，用于公司内部的文档管理、流程审批、任务分配等。
        - 新系统上线初期实行新旧系统并行运行，大家可通过新系统进行数据测试操作。
        - 测试期间，业务审核仍以旧系统流程为准，请务必严格遵照执行。
        - 此系统，泛微OA系统，即为上文提及旧系统
        """)

    with cols[1]:
        fw_img = "https://so1.360tres.com/t01b1fd8bc3bfca449c.jpg"
        fw_url = "http://218.18.233.27:8010"
        fc_card(title="0A-2025-入口",text="2019版OA | 实际流程请以此系统为准 | 部署于生命科学产业园B1机房",image=fw_img,url=fw_url)
    # ---------------------- 页脚 ----------------------
    fc_foot()

def fc_container_6():
    # ---------------------- 标题 ----------------------
    st.title("其它")
    st.divider()

    # ---------------------- 内容 ----------------------
    cols = st.columns(3)
    with cols[0]:
        fc_card(title="SCTZ-云盘",text="用于SCTZB 相关文件，包括合同、项目文档、客户信息的私有化云盘。",image="http://119.145.17.34:40061/i/2025/11/18/41dk2f.png",url="http://119.145.17.34:8501/")
        st.markdown(" ")
        fc_card(title="投控-打印机-配置相关材料",text="关于 投控-13楼、14楼打印机，搬迁后的连接。",image="https://globalimg.sucai999.com/preimg/DBC456/700/DBC456/154/15835bd95c4872416a39a18c3a762cd.jpg",url="https://www.yuque.com/leonzion/ogdboo/gipgzea09ie91ydm?singleDoc# 《投控打印机-连接》")

    with cols[1]:
        fc_card(title="Leyon-服务",text="存储项目文件与必要自建服务-私有化服务；仅允许内网访问。",image="http://119.145.17.34:40061/i/2025/11/18/3zk6jq.png",url="http://172.168.13.42:18090/")
        st.markdown(" ")
        fc_card(title="致远OA-开发手册",text="致远OA-开发手册-A8-N-协同管理软件。",image="https://ts1.tc.mm.bing.net/th/id/R-C.33cadd56bc7c6738d72e8bf6bc960ec3?rik=%2bB9Wv9ulg9J3Eg&riu=http%3a%2f%2fwww.zjseeyon.com%2fuploads%2fallimg%2f190621%2f2-1Z6212123210-L.jpg&ehk=CjbijTdgoUjdRMrdYdkiG7Dfk72mcZbef6wDjfErPEU%3d&risl=&pid=ImgRaw&r=0",url="https://share.fnnas.net/s/d0cffc2ecf524b9b92")
    with cols[2]:
        fc_card(title="Error-Cards",text="用于解决公司常见电脑或显示屏投屏问题。",image="http://119.145.17.34:40061/i/2025/11/18/4356pi.jpg",url="https://www.yuque.com/leonzion/ogdboo")
        st.markdown(" ")
        fc_card(title=" ... ",text="None",image="http://119.145.17.34:40061/i/2025/11/18/55redd.png",url="https://www.baidu.com/")
    # ---------------------- 页脚 ----------------------
    fc_foot()