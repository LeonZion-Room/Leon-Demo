import os
import uuid
import json
import streamlit as st
from urllib.parse import urlencode
from utils import ensure_storage, load_batches, save_batches, to_safe_filename, unique_filename, STORAGE_DIR

ensure_storage()

def require_auth():
    if "authed" not in st.session_state:
        st.session_state["authed"] = False
    if not st.session_state["authed"]:
        st.title("文件存储系统")
        pwd = st.text_input("请输入密码", type="password")
        if st.button("登录"):
            target = os.environ.get("FILEBOX_PASSWORD", "")
            if pwd and target and pwd == target:
                st.session_state["authed"] = True
                st.rerun()
            else:
                st.error("密码错误或未设置环境变量 FILEBOX_PASSWORD")
        st.stop()

def app_header():
    st.title("FileBox-Demo")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("拖拽或选择多文件上传，生成查看链接，支持重命名与下载")
    with col2:
        if st.button("退出登录"):
            st.session_state["authed"] = False
            st.rerun()

def upload_page():
    files = st.file_uploader("上传文件", accept_multiple_files=True)
    if st.button("保存并生成查看链接"):
        if not files:
            st.warning("请先选择文件")
            return
        batches = load_batches()
        batch_id = uuid.uuid4().hex
        batch_dir = os.path.join(STORAGE_DIR, f"batch_{batch_id}")
        os.makedirs(batch_dir, exist_ok=True)
        entries = []
        for f in files:
            safe = to_safe_filename(f.name)
            safe = unique_filename(batch_dir, safe)
            target_path = os.path.join(batch_dir, safe)
            with open(target_path, "wb") as out:
                out.write(f.getbuffer())
            entries.append({"name": f.name, "safe_name": safe, "path": target_path})
        batches[batch_id] = entries
        save_batches(batches)
        qp = urlencode({"batch": batch_id})
        link = f"http://localhost:8501/?{qp}"
        st.success("上传完成")
        st.link_button("查看链接", link)
        st.code(link)

def view_batch_page(batch_id):
    batches = load_batches()
    if batch_id not in batches:
        st.error("批次不存在")
        return
    entries = batches[batch_id]
    st.subheader("当前批次文件")
    with st.form("edit_form"):
        new_names = []
        for i, e in enumerate(entries):
            col1, col2, col3 = st.columns([4,3,3])
            with col1:
                nn = st.text_input("文件名称", value=e["name"], key=f"name_{i}")
                new_names.append(nn)
            with col2:
                url = f"http://localhost:8000/download/{batch_id}/{e['safe_name']}"
                st.write(url)
            with col3:
                st.link_button("下载", url)
        submitted = st.form_submit_button("保存更改")
        if submitted:
            batch_dir = os.path.join(STORAGE_DIR, f"batch_{batch_id}")
            changed = False
            for i, e in enumerate(entries):
                nn = new_names[i]
                if nn != e["name"]:
                    new_safe = to_safe_filename(nn)
                    new_safe = unique_filename(batch_dir, new_safe)
                    old_path = e["path"]
                    new_path = os.path.join(batch_dir, new_safe)
                    if os.path.exists(old_path):
                        os.replace(old_path, new_path)
                    e["name"] = nn
                    e["safe_name"] = new_safe
                    e["path"] = new_path
                    changed = True
            if changed:
                batches[batch_id] = entries
                save_batches(batches)
                st.success("已保存更改")
                st.rerun()
            else:
                st.info("无变更")

def main():
    require_auth()
    app_header()
    params = st.experimental_get_query_params()
    bid = params.get("batch", [None])[0]
    if bid:
        view_batch_page(bid)
    else:
        upload_page()

if __name__ == "__main__":
    main()