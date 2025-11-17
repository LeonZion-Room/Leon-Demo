import streamlit as st
import streamlit_extras
from streamlit.components.v1 import html
import streamlit as st
from streamlit.components.v1 import html


def fc_head():
    # 居中 占满容器 展示一张图片
    st.image("logo.jpg", use_container_width=True)
    st.markdown(" ")

    
def fc_card(title, text, image, url, img_width=200, img_height=120):
    st.markdown(
        f"""
        <div class="fc-card">
          <div class="fc-card-img-wrap" style="width:{img_width}px;height:{img_height}px;">
            <img class="fc-card-img" src="{image}" alt="card"/>
          </div>
          <div class="fc-card-content" style="min-height:{img_height}px;">
            <div class="fc-card-title">{title}</div>
            <div class="fc-card-text">{text}</div>
            <a class="fc-card-link" href="{url}" target="_blank">点击进入</a>
          </div>
        </div>
        <style>
          .fc-card{{
            display:flex;
            align-items:flex-start;
            gap:10px;
            width:100%;
            padding:12px;
            border-radius:12px;
            background:#ffffff;
            border:1px solid #e5e7eb;
            box-shadow:0 1px 2px rgba(0,0,0,0.03);
          }}
          .fc-card-img-wrap{{
            border-radius:20px;
            overflow:hidden;
            flex-shrink:0;
          }}
          .fc-card-img{{
            width:100%;
            height:100%;
            object-fit:cover;
            object-position:center;
            display:block;
          }}
          .fc-card-content{{
            display:flex;
            flex-direction:column;
            gap:6px;
            flex:1;
            min-width:0;
          }}
          .fc-card-title{{
            font-size:18px;
            line-height:1.3;
            height:1.3em;
            font-weight:600;
            color:#111827;
            overflow:hidden;
            white-space:nowrap;
            text-overflow:ellipsis;
          }}
          .fc-card-text{{
            font-size:14px;
            line-height:1.4;
            height:calc(1.4em * 2);
            color:#4b5563;
            overflow:hidden;
            display:-webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 2;
          }}
          .fc-card-link{{
            font-size:14px;
            color:#2563eb;
            text-decoration:none;
          }}
          .fc-card-link:hover{{
            text-decoration:underline;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def fc_carousel(slides, height=360, sec_per_slide=3, max_width=None, aspect_ratio=None, full_viewport=False):
    n = len(slides)
    duration = n * sec_per_slide
    steps = []
    for i in range(n):
        pct = round(i * 100 / n, 4)
        offset = round(i * (100 / n), 4)
        steps.append(f"{pct}% {{ transform: translateX(-{offset}%); }}")
    keyframes = " ".join(steps) + " 100% { transform: translateX(0%); }"
    slides_width = f"{n * 100}%"
    slide_basis = f"calc(100% / {n})"
    items = "".join([
        f"<div class='slide'><img src='{s['image']}'/><div class='overlay'><div class='overlay-box'><div class='overlay-title'>{s['title']}</div><div class='overlay-text'>{s['text']}</div><a class='overlay-link' href='{s['url']}' target='_blank'>点击进入</a></div></div></div>"
        for s in slides
    ])
    max_w_css = f"max-width:{max_width}px;" if max_width else ""
    size_css = (
        f"aspect-ratio:{aspect_ratio};height:auto;"
        if aspect_ratio
        else f"height:{height}px;"
    )
    html_height = (height + 20)
    if full_viewport:
        html_height = 800
    import uuid
    carousel_id = "fc_carousel_" + uuid.uuid4().hex
    html(
        f"""
        <div class='carousel' id='{carousel_id}'>
          <div class='slides'>
            {items}
          </div>
          <div class='nav prev' aria-label='上一张'>&#10094;</div>
          <div class='nav next' aria-label='下一张'>&#10095;</div>
        </div>
        <style>
          .carousel{{
            position:relative;
            width:100%;
            {max_w_css}
            {size_css}
            overflow:hidden;
            border-radius:12px;
            background:transparent;
          }}
          .slides{{
            display:flex;
            width:{slides_width};
            height:100%;
            transition: transform 0.6s ease;
          }}
          .slide{{
            width:{slide_basis};
            flex: 0 0 {slide_basis};
            height:100%;
            position:relative;
          }}
          .slide img{{
            width:100%;
            height:100%;
            object-fit:cover;
            object-position:center;
            display:block;
          }}
          .overlay{{
            position:absolute;
            left:0; right:0; bottom:0;
            height:25%;
            padding:0;
            background: linear-gradient(to top, rgba(0,0,0,0.6), rgba(0,0,0,0));
            color:#fff;
            display:flex;
            flex-direction:column;
            justify-content:flex-end;
            gap:0;
          }}
          .overlay-box{{
            background: rgba(0,0,0,0.35);
            backdrop-filter: blur(2px);
            border-radius:0;
            padding:12px;
            display:flex;
            flex-direction:column;
            gap:6px;
            width:100%;
            max-width:100%;
            height:auto;
            box-sizing:border-box;
          }}
          .overlay-title{{
            font-size: clamp(18px, 2.2vw, 28px);
            font-weight: 700;
            overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
          }}
          .overlay-text{{
            font-size: clamp(12px, 1.4vw, 16px);
            line-height:1.4;
            color:#e5e7eb;
            display:block;
            max-width:100%;
            overflow:hidden;
            white-space:nowrap;
            text-overflow:ellipsis;
          }}
          .overlay-link{{
            font-size:14px;
            color:#93c5fd;
            text-decoration:none;
            font-weight:600;
            align-self:flex-start;
            background: rgba(255,255,255,0.1);
            padding:6px 10px;
            border-radius:6px;
          }}
          .overlay-link:hover{{ text-decoration:underline; }}
          .nav{{
            position:absolute;
            top:50%;
            transform: translateY(-50%);
            width:40px; height:40px;
            border-radius:50%;
            background: rgba(0,0,0,0.35);
            color:#fff;
            display:flex; align-items:center; justify-content:center;
            cursor:pointer;
            user-select:none;
            z-index:10;
          }}
          .nav.prev{{ left:10px; }}
          .nav.next{{ right:10px; }}
        </style>
        <script>
        (function(){{
          var root = document.getElementById('{carousel_id}');
          if(!root) return;
          var slides = root.querySelector('.slides');
          var count = {n};
          var idx = 0;
          function render(){{
            var offset = (100 / count) * idx;
            slides.style.transform = 'translateX(-' + offset + '%)';
          }}
          function next(){{ idx = (idx + 1) % count; render(); }}
          function prev(){{ idx = (idx - 1 + count) % count; render(); }}
          var nextBtn = root.querySelector('.nav.next');
          var prevBtn = root.querySelector('.nav.prev');
          nextBtn.addEventListener('click', next);
          prevBtn.addEventListener('click', prev);
          var timer = null;
          function start(){{
            var sec = {sec_per_slide};
            if(sec > 0){{
              stop();
              timer = setInterval(next, sec * 1000);
            }}
          }}
          function stop(){{ if(timer){{ clearInterval(timer); timer=null; }} }}
          root.addEventListener('mouseenter', stop);
          root.addEventListener('mouseleave', start);
          render();
          start();
        }})();
        </script>
        """,
        height=html_height,
    )


def fc_hls_player(src, height=420, poster=None, autoplay=True, muted=True, controls=True):
    import uuid
    vid = "fc_hls_" + uuid.uuid4().hex
    poster_attr = f"poster='{poster}'" if poster else ""
    autoplay_attr = "autoplay" if autoplay else ""
    muted_attr = "muted" if muted else ""
    controls_attr = "controls" if controls else ""
    html(
        f"""
        <div id='{vid}_wrap' style='width:100%;height:{height}px;background:#000;border-radius:12px;overflow:hidden;'>
          <video id='{vid}' {poster_attr} {autoplay_attr} {muted_attr} {controls_attr} playsinline style='width:100%;height:100%;object-fit:contain;background:#000;'></video>
        </div>
        <script src='https://cdn.jsdelivr.net/npm/hls.js@latest'></script>
        <script>
          (function(){{
            var video = document.getElementById('{vid}');
            var src = '{src}';
            function play(){{ try{{ video.play(); }}catch(e){{}} }}
            if (window.Hls && window.Hls.isSupported()) {{
              var hls = new Hls({{ lowLatencyMode: true }});
              hls.loadSource(src);
              hls.attachMedia(video);
              hls.on(Hls.Events.MANIFEST_PARSED, function(){{ play(); }});
              hls.on(Hls.Events.ERROR, function(event, data){{ console.warn('HLS error', data); }});
            }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
              video.src = src;
              video.addEventListener('loadedmetadata', play);
            }} else {{
              console.warn('HLS not supported in this browser');
            }}
          }})();
        </script>
        """,
        height=height + 20,
    )



# ---------------------- 基础函数 ----------------------
def fc_foot():
    st.divider()
    cols = st.columns([8,14,2])
    with cols[0]:
        st.write("""- 地址：大鹏新区坝光海康路格兰云天-E栋-13楼""")
        st.write("""- 电话反馈：19580783095""")
        st.write("""- 微信反馈：shenzhen2024lyzlyz""")
    with cols[1]:
        st.markdown(
            """
            <div class="fc-links"><span>其它链接:</span>
            <a href="http://119.145.17.34:8501/" target="_blank">SCTZB-NAS</a>&nbsp; &nbsp; &nbsp; &nbsp;
            <a href="http://172.168.13.42:18090/" target="_blank">Leyon-Server</a>&nbsp; &nbsp;  &nbsp; &nbsp;
            <a href="https://www.yuque.com/leonzion/ogdboo" target="_blank">常见异常-工具集合</a>&nbsp; &nbsp; &nbsp; &nbsp;
            <a href="https://www.yuque.com/leonzion/ogdboo/gipgzea09ie91ydm?singleDoc#%20%E3%80%8A%E6%8A%95%E6%8E%A7%E6%89%93%E5%8D%B0%E6%9C%BA-%E8%BF%9E%E6%8E%A5%E3%80%8B" target="_blank">投控打印机配置与连接</a>&nbsp; &nbsp; &nbsp; &nbsp;
            </div>
            <style>
            .fc-links a{color:#111827;text-decoration:none;font-weight:600;}
            .fc-links a:hover{text-decoration:underline;color:#111827;}
            .fc-links span{font-weight:600;color:#111827;margin-right:8px;}
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="fc-links"><span>开发日志:</span>
            <a href="http://dptk.site" target="_blank">http://dptk.site</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="fc-links"><span>回到首页:</span>
            <a href="http://dptk.site" target="_blank">http://dptk.site</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown("**详情请联系**")
        st.image("mine.png", use_container_width=True)

def render_carousel(
    slides,
    height=360,
    sec_per_slide=3,
    max_width=1080,
    border_radius=12,
    page_title="Carousel Demo",
    layout="wide"
):
    """
    渲染一个美观的自动轮播组件

    参数:
    slides (list): 轮播项列表，每个项是包含以下键的字典：
        - image (str): 图片URL
        - title (str): 标题文本
        - text (str): 描述文本
        - url (str): 跳转链接
    height (int): 轮播组件高度（像素），默认360
    sec_per_slide (int): 每张幻灯片显示时间（秒），默认3
    max_width (int): 轮播组件最大宽度（像素），默认1080
    border_radius (int): 圆角大小（像素），默认12
    page_title (str): 页面标题，默认"Carousel Demo"
    layout (str): 页面布局，默认"wide"（可选："centered"或"wide"）
    """
    # 设置页面配置
    st.set_page_config(page_title=page_title, layout=layout)
    
    n = len(slides)
    if n == 0:
        st.warning("轮播列表不能为空！")
        return
    
    duration = n * sec_per_slide
    
    # 生成关键帧动画
    steps = []
    for i in range(n):
        pct = round(i * 100 / n, 4)
        offset = round(i * (100 / n), 4)
        steps.append(f"{pct}% {{ transform: translateX(-{offset}%); }}")
    keyframes = " ".join(steps) + " 100% { transform: translateX(0%); }"
    
    slides_width = f"{n * 100}%"
    slide_basis = f"calc(100% / {n})"
    
    # 生成轮播项HTML
    items = "".join([
        f"<div class='slide'>"
        f"<img src='{s['image']}' alt='{s.get('title', 'slide')}'/>"
        f"<div class='overlay'>"
        f"<div class='overlay-title'>{s['title']}</div>"
        f"<div class='overlay-text'>{s['text']}</div>"
        f"<a class='overlay-link' href='{s['url']}' target='_blank'>点击进入</a>"
        f"</div></div>"
        for s in slides
    ])
    
    # 渲染HTML组件
    html(
        f"""
        <div class='carousel'>
          <div class='slides'>
            {items}
          </div>
        </div>
        <style>
          .carousel{{
            position:relative;
            width:100%;
            max-width:{max_width}px;
            height:{height}px;
            overflow:hidden;
            border-radius:{border_radius}px;
            background:transparent;
            margin:0 auto;
          }}
          .slides{{
            display:flex;
            width:{slides_width};
            height:100%;
            animation: fcSlide {duration}s infinite;
            transition-timing-function: ease-in-out;
          }}
          .slide{{
            width:{slide_basis};
            flex: 0 0 {slide_basis};
            height:100%;
            position:relative;
          }}
          .slide img{{
            width:100%;
            height:100%;
            object-fit:cover;
            object-position:center;
            display:block;
          }}
          .overlay{{
            position:absolute;
            left:0; right:0; bottom:0;
            padding:16px;
            background: linear-gradient(to top, rgba(0,0,0,0.55), rgba(0,0,0,0.0) 70%);
            color:#fff;
            display:flex;
            flex-direction:column;
            gap:8px;
          }}
          .overlay-title{{
            font-size: clamp(18px, 2.2vw, 28px);
            font-weight: 700;
            overflow:hidden; 
            white-space:nowrap; 
            text-overflow:ellipsis;
          }}
          .overlay-text{{
            font-size: clamp(12px, 1.4vw, 16px);
            line-height:1.4;
            color:#e5e7eb;
            overflow:hidden; 
            display:-webkit-box; 
            -webkit-box-orient: vertical; 
            -webkit-line-clamp: 2;
          }}
          .overlay-link{{
            font-size:14px;
            color:#93c5fd;
            text-decoration:none;
            font-weight:600;
            align-self:flex-start;
            background: rgba(255,255,255,0.1);
            padding:6px 10px;
            border-radius:6px;
            transition: all 0.3s ease;
          }}
          .overlay-link:hover{{ 
            text-decoration:underline;
            background: rgba(255,255,255,0.2);
          }}
          @keyframes fcSlide{{ {keyframes} }}
        </style>
        """,
        height=height + 20,
    )