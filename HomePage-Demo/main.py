import os
import sys
import json
import uuid
from pathlib import Path
import streamlit as st
from streamlit_extras.grid import grid
from streamlit_extras.stylable_container import stylable_container

APP_TITLE = "主页"
DATA_DIR = Path("data")
DATA_PATH = DATA_DIR / "homepage.json"
IMAGES_DIR = Path("assets/images")

def _load_data():
    if not DATA_PATH.exists():
        return {
            "columns": 3,
            "groups": [
                {
                    "id": uuid.uuid4().hex,
                    "name": "示例组",
                    "description": "示例卡片集合",
                    "cards": [
                        {
                            "id": uuid.uuid4().hex,
                            "title": "Streamlit 官网",
                            "description": "快速构建数据应用",
                            "button_text": "访问",
                            "url": "https://streamlit.io",
                            "image": "https://picsum.photos/800/450",
                            "order": 0,
                        }
                    ],
                }
            ],
        }
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _get_group(data, gid):
    for g in data["groups"]:
        if g["id"] == gid:
            return g
    return None

def _ensure_state():
    if "data" not in st.session_state:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        st.session_state.data = _load_data()
        if st.session_state.data.get("groups"):
            st.session_state.selected_group_id = st.session_state.data["groups"][0]["id"]
        else:
            st.session_state.selected_group_id = None
    if "columns" not in st.session_state:
        st.session_state.columns = st.session_state.data.get("columns", 3)

def _set_selected_group(gid):
    st.session_state.selected_group_id = gid

def _add_group(name, desc):
    g = {"id": uuid.uuid4().hex, "name": name, "description": desc, "cards": []}
    st.session_state.data["groups"].append(g)
    st.session_state.selected_group_id = g["id"]
    _save_data(st.session_state.data)

def _update_group(gid, name, desc):
    g = _get_group(st.session_state.data, gid)
    if not g:
        return
    g["name"] = name
    g["description"] = desc
    _save_data(st.session_state.data)

def _delete_group(gid):
    st.session_state.data["groups"] = [g for g in st.session_state.data["groups"] if g["id"] != gid]
    if st.session_state.data["groups"]:
        st.session_state.selected_group_id = st.session_state.data["groups"][0]["id"]
    else:
        st.session_state.selected_group_id = None
    _save_data(st.session_state.data)

def _add_card(gid, title, desc, btn_text, url, image_file, image_url):
    image_path = None
    if image_file is not None:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}_{image_file.name}"
        p = IMAGES_DIR / filename
        with open(p, "wb") as f:
            f.write(image_file.getbuffer())
        image_path = str(p.as_posix())
    elif image_url:
        image_path = image_url
    g = _get_group(st.session_state.data, gid)
    if not g:
        return
    order = 0
    if g["cards"]:
        order = max([c.get("order", 0) for c in g["cards"]]) + 1
    c = {
        "id": uuid.uuid4().hex,
        "title": title,
        "description": desc,
        "button_text": btn_text or "打开",
        "url": url,
        "image": image_path,
        "order": order,
    }
    g["cards"].append(c)
    _save_data(st.session_state.data)

def _update_card(gid, cid, title, desc, btn_text, url, image_file, image_url):
    g = _get_group(st.session_state.data, gid)
    if not g:
        return
    for c in g["cards"]:
        if c["id"] == cid:
            c["title"] = title
            c["description"] = desc
            c["button_text"] = btn_text or "打开"
            c["url"] = url
            if image_file is not None:
                IMAGES_DIR.mkdir(parents=True, exist_ok=True)
                filename = f"{uuid.uuid4().hex}_{image_file.name}"
                p = IMAGES_DIR / filename
                with open(p, "wb") as f:
                    f.write(image_file.getbuffer())
                c["image"] = str(p.as_posix())
            elif image_url:
                c["image"] = image_url
            _save_data(st.session_state.data)
            return

def _delete_card(gid, cid):
    g = _get_group(st.session_state.data, gid)
    if not g:
        return
    g["cards"] = [c for c in g["cards"] if c["id"] != cid]
    for i, c in enumerate(sorted(g["cards"], key=lambda x: x.get("order", 0))):
        c["order"] = i
    _save_data(st.session_state.data)

def _move_card(gid, cid, direction):
    g = _get_group(st.session_state.data, gid)
    if not g:
        return
    cards = sorted(g["cards"], key=lambda x: x.get("order", 0))
    idx = next((i for i, c in enumerate(cards) if c["id"] == cid), None)
    if idx is None:
        return
    if direction == "up" and idx > 0:
        cards[idx]["order"], cards[idx - 1]["order"] = cards[idx - 1]["order"], cards[idx]["order"]
    if direction == "down" and idx < len(cards) - 1:
        cards[idx]["order"], cards[idx + 1]["order"] = cards[idx + 1]["order"], cards[idx]["order"]
    cards = sorted(cards, key=lambda x: x.get("order", 0))
    for i, c in enumerate(cards):
        c["order"] = i
    g["cards"] = cards
    _save_data(st.session_state.data)

def _render_card(c):
    with stylable_container(
        key=f"card-{c['id']}",
        css_styles="""
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 12px;
        background: white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        transition: transform 150ms ease, box-shadow 150ms ease;
    """,
    ):
        if c.get("image"):
            st.image(c["image"], use_container_width=True)
        st.subheader(c.get("title") or "")
        st.write(c.get("description") or "")
        cols = st.columns([1, 1, 1, 2])
        with cols[0]:
            st.link_button(c.get("button_text") or "打开", c.get("url") or "#", use_container_width=True)
        with cols[1]:
            if st.button("上移", key=f"up-{c['id']}"):
                _move_card(st.session_state.selected_group_id, c["id"], "up")
                st.rerun()
        with cols[2]:
            if st.button("下移", key=f"down-{c['id']}"):
                _move_card(st.session_state.selected_group_id, c["id"], "down")
                st.rerun()
        with cols[3]:
            e1, e2 = st.columns(2)
            with e1:
                if st.button("编辑", key=f"edit-{c['id']}"):
                    st.session_state.editing_card_id = c["id"]
                    st.rerun()
            with e2:
                if st.button("删除", key=f"del-{c['id']}"):
                    _delete_card(st.session_state.selected_group_id, c["id"])
                    st.rerun()

def _render_edit_card_form(gid, cid):
    g = _get_group(st.session_state.data, gid)
    if not g:
        return
    c = next((x for x in g["cards"] if x["id"] == cid), None)
    if not c:
        return
    with st.form(key=f"edit-form-{cid}"):
        t = st.text_input("标题", value=c.get("title") or "")
        d = st.text_area("描述", value=c.get("description") or "")
        b = st.text_input("按钮文字", value=c.get("button_text") or "打开")
        u = st.text_input("链接地址", value=c.get("url") or "")
        img_file = st.file_uploader("上传图片", type=["png", "jpg", "jpeg", "gif"], accept_multiple_files=False)
        img_url = st.text_input("图片链接", value=c.get("image") if isinstance(c.get("image"), str) and c.get("image", "").startswith("http") else "")
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            saved = st.form_submit_button("保存")
        with s_col2:
            cancel = st.form_submit_button("取消")
        if saved:
            _update_card(gid, cid, t, d, b, u, img_file, img_url)
            st.session_state.editing_card_id = None
            st.rerun()
        if cancel:
            st.session_state.editing_card_id = None
            st.rerun()

def app():
    st.set_page_config(page_title=APP_TITLE, page_icon="🏠", layout="wide")
    _ensure_state()
    st.title(APP_TITLE)
    left, right = st.columns([1, 3])
    with left:
        st.header("分组")
        groups = st.session_state.data.get("groups", [])
        names = [g["name"] for g in groups]
        ids = [g["id"] for g in groups]
        if ids:
            idx = ids.index(st.session_state.selected_group_id) if st.session_state.selected_group_id in ids else 0
            selected = st.radio("选择分组", options=ids, index=idx, key="group-select", format_func=lambda x: groups[ids.index(x)]["name"])
            if selected != st.session_state.selected_group_id:
                _set_selected_group(selected)
        with st.form("add-group"):
            ng = st.text_input("新分组名称")
            nd = st.text_input("新分组描述")
            add_ok = st.form_submit_button("添加分组")
            if add_ok and ng.strip():
                _add_group(ng.strip(), nd.strip())
                st.rerun()
        if st.session_state.selected_group_id:
            g = _get_group(st.session_state.data, st.session_state.selected_group_id)
            with st.form("edit-group"):
                eg = st.text_input("分组名称", value=g["name"])
                ed = st.text_input("分组描述", value=g.get("description", ""))
                ec1, ec2 = st.columns(2)
                with ec1:
                    ok = st.form_submit_button("保存")
                with ec2:
                    del_ok = st.form_submit_button("删除分组")
                if ok:
                    _update_group(g["id"], eg.strip(), ed.strip())
                    st.rerun()
                if del_ok:
                    _delete_group(g["id"])
                    st.rerun()
        st.header("布局")
        cols = st.slider("分栏数", min_value=1, max_value=6, value=st.session_state.columns)
        if cols != st.session_state.columns:
            st.session_state.columns = cols
            st.session_state.data["columns"] = cols
            _save_data(st.session_state.data)
    with right:
        if not st.session_state.selected_group_id:
            st.info("请创建或选择一个分组")
        else:
            g = _get_group(st.session_state.data, st.session_state.selected_group_id)
            st.header(g["name"])
            st.caption(g.get("description", ""))
            with st.form("add-card"):
                t = st.text_input("标题")
                d = st.text_area("描述")
                b = st.text_input("按钮文字", value="打开")
                u = st.text_input("链接地址")
                img_file = st.file_uploader("上传图片", type=["png", "jpg", "jpeg", "gif"], accept_multiple_files=False)
                img_url = st.text_input("图片链接")
                cc1, cc2 = st.columns(2)
                with cc1:
                    ok = st.form_submit_button("添加卡片")
                with cc2:
                    reset = st.form_submit_button("清空")
                if ok and t.strip():
                    _add_card(g["id"], t.strip(), d.strip(), b.strip(), u.strip(), img_file, img_url.strip())
                    st.rerun()
            cards = sorted(g.get("cards", []), key=lambda x: x.get("order", 0))
            gr = grid(st.session_state.columns, vertical_align="top")
            for c in cards:
                with gr.container():
                    if st.session_state.get("editing_card_id") == c["id"]:
                        _render_edit_card_form(g["id"], c["id"])
                    else:
                        _render_card(c)

if __name__ == "__main__":
    try:
        import streamlit.web.cli as stcli
        sys.argv = ["streamlit", "run", str(Path(__file__).absolute())]
        sys.exit(stcli.main())
    except Exception:
        app()