import json
import os
import uuid
import pandas as pd
import streamlit as st
from streamlit_sortables import sort_items

DATA_PATH = os.path.join("data", "site.json")

def load_data():
    if not os.path.exists(DATA_PATH):
        return {"site": {"title": "我的博客", "theme": {}}, "pages": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def new_section(section_type, cols=2):
    sid = uuid.uuid4().hex[:8]
    if section_type == "row":
        return {
            "id": sid,
            "type": "row",
            "columns": [
                {"id": uuid.uuid4().hex[:8], "width": 1, "items": []}
                for _ in range(int(cols))
            ],
        }
    if section_type == "title":
        return {"id": sid, "type": "title", "text": "标题"}
    if section_type == "subheader":
        return {"id": sid, "type": "subheader", "text": "子标题"}
    if section_type == "header":
        return {"id": sid, "type": "header", "text": "标题"}
    if section_type == "paragraph":
        return {"id": sid, "type": "paragraph", "text": "正文"}
    if section_type == "markdown":
        return {"id": sid, "type": "markdown", "text": "**Markdown**"}
    if section_type == "image":
        return {"id": sid, "type": "image", "url": "", "caption": ""}
    if section_type == "code":
        return {"id": sid, "type": "code", "language": "python", "content": "print('hello')"}
    if section_type == "divider":
        return {"id": sid, "type": "divider"}
    if section_type == "button":
        return {"id": sid, "type": "button", "label": "按钮"}
    if section_type == "checkbox":
        return {"id": sid, "type": "checkbox", "label": "选项", "value": False}
    if section_type == "text_input":
        return {"id": sid, "type": "text_input", "label": "文本", "value": "", "placeholder": ""}
    if section_type == "number_input":
        return {"id": sid, "type": "number_input", "label": "数字", "value": 0, "min": 0, "max": 100, "step": 1}
    if section_type == "selectbox":
        return {"id": sid, "type": "selectbox", "label": "选择", "options": ["A", "B", "C"], "index": 0}
    if section_type == "slider":
        return {"id": sid, "type": "slider", "label": "滑块", "min": 0, "max": 100, "value": 50, "step": 1}
    if section_type == "date_input":
        return {"id": sid, "type": "date_input", "label": "日期"}
    if section_type == "dataframe":
        return {"id": sid, "type": "dataframe", "data": [{"A": 1, "B": 2}, {"A": 3, "B": 4}]}
    return {"id": sid, "type": "paragraph", "text": ""}

def render_item(container, item):
    t = item.get("type")
    if t == "title":
        container.title(item.get("text", ""))
    elif t == "subheader":
        container.subheader(item.get("text", ""))
    elif t == "header":
        container.header(item.get("text", ""))
    elif t == "paragraph":
        container.write(item.get("text", ""))
    elif t == "markdown":
        container.markdown(item.get("text", ""))
    elif t == "image":
        container.image(item.get("url", ""), caption=item.get("caption", ""))
    elif t == "code":
        container.code(item.get("content", ""), language=item.get("language", "text"))
    elif t == "divider":
        container.divider()
    elif t == "button":
        container.button(item.get("label", ""))
    elif t == "checkbox":
        container.checkbox(item.get("label", ""), value=item.get("value", False))
    elif t == "text_input":
        container.text_input(item.get("label", ""), value=item.get("value", ""), placeholder=item.get("placeholder", ""))
    elif t == "number_input":
        container.number_input(item.get("label", ""), value=item.get("value", 0), min_value=item.get("min", None), max_value=item.get("max", None), step=item.get("step", 1))
    elif t == "selectbox":
        container.selectbox(item.get("label", ""), options=item.get("options", []), index=item.get("index", 0))
    elif t == "slider":
        container.slider(item.get("label", ""), min_value=item.get("min", 0), max_value=item.get("max", 100), value=item.get("value", 50), step=item.get("step", 1))
    elif t == "date_input":
        container.date_input(item.get("label", ""))
    elif t == "dataframe":
        try:
            container.dataframe(pd.DataFrame(item.get("data", [])))
        except Exception:
            container.write(item.get("data", []))

def edit_item(item):
    t = item.get("type")
    if t == "title":
        item["text"] = st.text_input("文本", value=item.get("text", ""), key=f"text_{item['id']}")
        return
    if t == "subheader":
        item["text"] = st.text_input("文本", value=item.get("text", ""), key=f"text_{item['id']}")
        return
    if t == "header":
        item["text"] = st.text_input("文本", value=item.get("text", ""), key=f"text_{item['id']}")
    elif t == "paragraph":
        item["text"] = st.text_area("文本", value=item.get("text", ""), key=f"text_{item['id']}")
    elif t == "markdown":
        item["text"] = st.text_area("Markdown", value=item.get("text", ""), key=f"md_{item['id']}")
    elif t == "image":
        item["url"] = st.text_input("图片URL", value=item.get("url", ""), key=f"url_{item['id']}")
        item["caption"] = st.text_input("说明", value=item.get("caption", ""), key=f"cap_{item['id']}")
    elif t == "code":
        item["language"] = st.selectbox("语言", options=["python", "javascript", "text", "json", "markdown"], index=["python", "javascript", "text", "json", "markdown"].index(item.get("language", "python")), key=f"lang_{item['id']}")
        item["content"] = st.text_area("代码", value=item.get("content", ""), key=f"code_{item['id']}")
    elif t == "divider":
        pass
    elif t == "button":
        item["label"] = st.text_input("标签", value=item.get("label", ""), key=f"lbl_{item['id']}")
    elif t == "checkbox":
        item["label"] = st.text_input("标签", value=item.get("label", ""), key=f"lbl_{item['id']}")
        item["value"] = st.checkbox("默认选中", value=item.get("value", False), key=f"val_{item['id']}")
    elif t == "text_input":
        item["label"] = st.text_input("标签", value=item.get("label", ""), key=f"lbl_{item['id']}")
        item["value"] = st.text_input("默认值", value=item.get("value", ""), key=f"val_{item['id']}")
        item["placeholder"] = st.text_input("占位符", value=item.get("placeholder", ""), key=f"ph_{item['id']}")
    elif t == "number_input":
        item["label"] = st.text_input("标签", value=item.get("label", ""), key=f"lbl_{item['id']}")
        item["value"] = st.number_input("默认值", value=item.get("value", 0), key=f"val_{item['id']}")
        item["min"] = st.number_input("最小值", value=item.get("min", 0), key=f"min_{item['id']}")
        item["max"] = st.number_input("最大值", value=item.get("max", 100), key=f"max_{item['id']}")
        item["step"] = st.number_input("步长", value=item.get("step", 1), key=f"step_{item['id']}")
    elif t == "selectbox":
        item["label"] = st.text_input("标签", value=item.get("label", ""), key=f"lbl_{item['id']}")
        opts_text = ",".join(item.get("options", []))
        opts_text = st.text_area("选项(逗号分隔)", value=opts_text, key=f"opts_{item['id']}")
        item["options"] = [o.strip() for o in opts_text.split(",") if o.strip()]
        item["index"] = st.number_input("默认索引", value=item.get("index", 0), min_value=0, max_value=max(len(item["options"]) - 1, 0), step=1, key=f"idx_{item['id']}")
    elif t == "slider":
        item["label"] = st.text_input("标签", value=item.get("label", ""), key=f"lbl_{item['id']}")
        item["min"] = st.number_input("最小值", value=item.get("min", 0), key=f"min_{item['id']}")
        item["max"] = st.number_input("最大值", value=item.get("max", 100), key=f"max_{item['id']}")
        item["value"] = st.number_input("默认值", value=item.get("value", 50), key=f"val_{item['id']}")
        item["step"] = st.number_input("步长", value=item.get("step", 1), key=f"step_{item['id']}")
    elif t == "date_input":
        item["label"] = st.text_input("标签", value=item.get("label", ""), key=f"lbl_{item['id']}")
    elif t == "dataframe":
        txt = st.text_area("数据(JSON)", value=json.dumps(item.get("data", []), ensure_ascii=False), key=f"df_{item['id']}")
        try:
            item["data"] = json.loads(txt)
        except Exception:
            pass

def all_types():
    return [
        "title",
        "header",
        "subheader",
        "paragraph",
        "markdown",
        "image",
        "code",
        "divider",
        "button",
        "checkbox",
        "text_input",
        "number_input",
        "selectbox",
        "slider",
        "date_input",
        "dataframe",
        "row",
    ]

def slash_palette(list_ref, insert_index, key):
    txt_key = f"sl_{key}"
    sel_key = f"sl_sel_{key}"
    v = st.text_input("输入 / 选择组件", value=st.session_state.get(txt_key, ""), key=txt_key)
    term = v[1:] if v.startswith("/") else v
    choices = [t for t in all_types() if term.lower() in t.lower()] or all_types()
    sel = st.selectbox("组件", options=choices, index=0, key=sel_key)
    if st.button("插入", key=f"sl_add_{key}"):
        list_ref.insert(insert_index, new_section(sel))
        st.session_state[txt_key] = ""

def render_preview(page):
    st.subheader(page.get("title", ""))
    for s in page.get("sections", []):
        if s.get("type") == "row":
            cols = s.get("columns", [])
            widths = [c.get("width", 1) for c in cols]
            containers = st.columns(widths)
            for i, c in enumerate(cols):
                for item in c.get("items", []):
                    render_item(containers[i], item)
        else:
            render_item(st, s)

def render_editor(data):
    site = data.setdefault("site", {})
    pages = data.setdefault("pages", [])
    site_title = st.sidebar.text_input("站点标题", value=site.get("title", ""))
    site["title"] = site_title
    page_titles = [p.get("title", p.get("id", "")) for p in pages]
    page_idx = st.sidebar.selectbox("选择页面", options=list(range(len(pages))), format_func=lambda i: page_titles[i] if pages else "", index=0 if pages else None)
    add_page = st.sidebar.button("新建页面")
    if add_page or not pages:
        pages.append({"id": uuid.uuid4().hex[:8], "title": "未命名页面", "sections": []})
        page_idx = len(pages) - 1
    page = pages[page_idx]
    page["title"] = st.text_input("页面标题", value=page.get("title", ""), key=f"title_{page['id']}")
    sections = page.setdefault("sections", [])
    labels = [f"{s['id']}|{s['type']}" for s in sections]
    st.write("拖拽排序")
    sorted_labels = sort_items(labels, direction="vertical", key=f"sort_{page['id']}")
    if isinstance(sorted_labels, list) and len(sorted_labels) == len(sections):
        mapping = {lab.split("|")[0]: i for i, lab in enumerate(sorted_labels)}
        sections.sort(key=lambda s: mapping.get(s["id"], 0))
    slash_palette(sections, 0, f"page_top_{page['id']}")
    to_delete = []
    for s in sections:
        render_item(st, s) if s.get("type") != "row" else None
        with st.expander(f"{s['type']} - {s['id']}"):
            if s["type"] == "row":
                cols = s.setdefault("columns", [])
                widths = []
                for i, c in enumerate(cols):
                    w = st.number_input(f"列{i+1}宽度", value=float(c.get("width", 1)), key=f"w_{s['id']}_{c['id']}")
                    c["width"] = w
                    widths.append(w)
                containers_data = [
                    {"header": f"列 {i+1}", "items": [f"{itm['id']}|{itm['type']}" for itm in c.get("items", [])]}
                    for i, c in enumerate(cols)
                ]
                sorted_containers = sort_items(containers_data, multi_containers=True, key=f"mc_{s['id']}")
                if isinstance(sorted_containers, list) and len(sorted_containers) == len(cols):
                    id_map = {}
                    for c in cols:
                        for itm in c.get("items", []):
                            id_map[itm["id"]] = itm
                    for i, cont in enumerate(sorted_containers):
                        new_items = []
                        for lab in cont.get("items", []):
                            iid = lab.split("|")[0]
                            if iid in id_map:
                                new_items.append(id_map[iid])
                        cols[i]["items"] = new_items
                for idx, c in enumerate(cols):
                    st.write(f"列 {idx+1}")
                    del_ids = []
                    for j, itm in enumerate(c.get("items", [])):
                        render_item(st, itm)
                        with st.expander(f"{itm['type']} - {itm['id']}"):
                            edit_item(itm)
                            if st.button("删除", key=f"del_{itm['id']}"):
                                del_ids.append(itm["id"]) 
                        slash_palette(c.setdefault("items", []), j + 1, f"col_{s['id']}_{c['id']}_{itm['id']}")
                    if del_ids:
                        c["items"] = [x for x in c.get("items", []) if x["id"] not in del_ids]
                    slash_palette(c.setdefault("items", []), 0, f"col_top_{s['id']}_{c['id']}")
                    new_t = st.selectbox("添加组件", options=["header", "paragraph", "markdown", "image", "code", "button", "checkbox", "text_input", "number_input", "selectbox", "slider", "date_input", "dataframe"], key=f"add_col_{s['id']}_{c['id']}")
                    if st.button("添加", key=f"btn_add_col_{s['id']}_{c['id']}"):
                        c.setdefault("items", []).append(new_section(new_t))
                if st.button("新增列", key=f"add_col_{s['id']}"):
                    cols.append({"id": uuid.uuid4().hex[:8], "width": 1, "items": []})
                if len(cols) > 1 and st.button("删除最后一列", key=f"rm_last_col_{s['id']}"):
                    if not cols[-1].get("items"):
                        cols.pop()
            else:
                edit_item(s)
            if st.button("删除", key=f"del_{s['id']}"):
                to_delete.append(s["id"])
        slash_palette(sections, sections.index(s) + 1, f"page_{page['id']}_{s['id']}")
    if to_delete:
        page["sections"] = [s for s in sections if s["id"] not in to_delete]
    st.divider()
    new_type = st.selectbox("添加组件", options=["title", "header", "subheader", "paragraph", "markdown", "image", "code", "divider", "button", "checkbox", "text_input", "number_input", "selectbox", "slider", "date_input", "dataframe", "row"], key=f"add_{page['id']}")
    row_cols = st.number_input("新行列数", min_value=2, max_value=6, value=2, step=1, key=f"row_cols_{page['id']}")
    if st.button("添加", key=f"btn_add_{page['id']}"):
        if new_type == "row":
            sections.append(new_section("row", cols=row_cols))
        else:
            sections.append(new_section(new_type))
    if st.button("保存到 JSON"):
        save_data(data)
        st.success("已保存")

def main():
    data = load_data()
    st.set_page_config(page_title=data.get("site", {}).get("title", "我的博客"), layout="wide")
    mode = st.sidebar.radio("模式", ["编辑", "预览"], index=0)
    pages = data.get("pages", [])
    if not pages:
        data["pages"] = [{"id": uuid.uuid4().hex[:8], "title": "未命名页面", "sections": []}]
        save_data(data)
        pages = data["pages"]
    page_titles = [p.get("title", p.get("id", "")) for p in pages]
    sel = st.sidebar.selectbox("页面", options=list(range(len(pages))), format_func=lambda i: page_titles[i], index=0)
    if mode == "编辑":
        render_editor(data)
    else:
        render_preview(pages[sel])

if __name__ == "__main__":
    main()