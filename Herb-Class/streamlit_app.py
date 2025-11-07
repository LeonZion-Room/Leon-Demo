import os
import io
import zipfile
import time
from typing import List, Tuple

import streamlit as st
from PIL import Image
import torch

from infer import load_model, make_transform


st.set_page_config(page_title='Herb Classifier', layout='wide')
st.title('草药图片分类系统 (CPU)')


def get_model(model_path: str):
    if 'model_cache' not in st.session_state or st.session_state.get('model_path') != model_path:
        model, class_names, cfg = load_model(model_path)
        st.session_state['model_cache'] = (model, class_names, cfg)
        st.session_state['model_path'] = model_path
    return st.session_state['model_cache']


def classify_pil_image(img: Image.Image, model_path: str) -> Tuple[str, float]:
    model, class_names, cfg = get_model(model_path)
    tf = make_transform(img_size=int(cfg.get('img_size', 224)))
    x = tf(img.convert('RGB')).unsqueeze(0)
    with torch.no_grad():
        logits = model(x)
        prob = torch.softmax(logits, dim=1)
        pred = prob.argmax(dim=1).item()
        conf = float(prob[0, pred].item())
    return class_names[pred], conf


st.sidebar.header('设置')
model_path = st.sidebar.text_input('模型路径', value=os.path.join('models', 'best.pth'))
st.sidebar.info('请先通过训练生成 best.pth，再在此加载。')

with st.expander('帮助与说明'):
    st.markdown('- 上传单张图片可即时得到分类结果并显示图片。')
    st.markdown('- 上传 zip 压缩包后，自动解压并展示其中图片，点击查看详情（路径与分类结果）。')
    st.markdown('- 如模型较大或首次加载较慢，请耐心等待。')
    # 展示一个 API 帮助示例
    st.help(zipfile.ZipFile)

tab1, tab2 = st.tabs(['单张图片', '压缩包批量'])

with tab1:
    st.subheader('上传并分类单张图片')
    file = st.file_uploader('选择图片文件', type=['jpg', 'jpeg', 'png', 'bmp', 'webp'])
    if file is not None:
        img = Image.open(io.BytesIO(file.read()))
        st.image(img, caption='上传的图片', use_column_width=True)
        if os.path.isfile(model_path):
            pred, conf = classify_pil_image(img, model_path)
            st.success(f'分类结果：{pred}，置信度：{conf:.4f}')
        else:
            st.error(f'未找到模型文件：{model_path}')

with tab2:
    st.subheader('上传 zip 压缩包并批量分类')
    zip_file = st.file_uploader('选择 zip 文件', type=['zip'])
    if zip_file is not None:
        tmp_root = os.path.join('tmp_uploads')
        os.makedirs(tmp_root, exist_ok=True)
        # 用时间戳隔离子目录
        subdir = os.path.join(tmp_root, f'zip_{int(time.time())}')
        os.makedirs(subdir, exist_ok=True)
        # 解压
        with zipfile.ZipFile(io.BytesIO(zip_file.read())) as zf:
            zf.extractall(subdir)
        st.info(f'已解压到：{subdir}')

        # 收集图片
        image_paths: List[str] = []
        for root, _dirs, files in os.walk(subdir):
            for name in files:
                if name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
                    image_paths.append(os.path.join(root, name))
        image_paths.sort()

        if len(image_paths) == 0:
            st.warning('压缩包内未找到图片。')
        else:
            st.write(f'找到 {len(image_paths)} 张图片。')

            # 展示图片网格，每张图附查看按钮
            cols = st.columns(5)
            for i, p in enumerate(image_paths):
                with cols[i % 5]:
                    try:
                        img = Image.open(p)
                        st.image(img, caption=os.path.basename(p))
                        if st.button('查看详情', key=f'view_{i}'):
                            if os.path.isfile(model_path):
                                pred, conf = classify_pil_image(img, model_path)
                                st.write(f'路径：{p}')
                                st.success(f'分类结果：{pred}，置信度：{conf:.4f}')
                            else:
                                st.error(f'未找到模型文件：{model_path}')
                    except Exception as e:
                        st.error(f'加载图片失败：{p}，错误：{e}')