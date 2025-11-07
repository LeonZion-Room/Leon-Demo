import streamlit as st
from typing import List, Dict, Any
import uuid
import json

# 尝试导入拖拽排序组件（streamlit-draggable-list）
try:
    from st_draggable_list import DraggableList
    DRAGGABLE_AVAILABLE = True
except Exception:
    DRAGGABLE_AVAILABLE = False


# 组件定义：类型 -> 参数定义（用于填空设置）
COMPONENT_DEFS: Dict[str, Dict[str, Any]] = {
    "markdown": {
        "label": "Markdown",
        "params": [
            {"key": "content", "label": "内容（Markdown）", "type": "text_area", "default": "## 标题\n这是一段说明。"},
        ],
    },
    "header": {
        "label": "Header",
        "params": [
            {"key": "text", "label": "标题文本", "type": "text_input", "default": "页面标题"},
        ],
    },
    "subheader": {
        "label": "Subheader",
        "params": [
            {"key": "text", "label": "子标题文本", "type": "text_input", "default": "分区标题"},
        ],
    },
    "text": {
        "label": "Text",
        "params": [
            {"key": "text", "label": "文本内容", "type": "text_input", "default": "一段普通文本"},
        ],
    },
    "divider": {
        "label": "Divider",
        "params": [],
    },
    "text_input": {
        "label": "Text Input",
        "params": [
            {"key": "label", "label": "标签", "type": "text_input", "default": "请输入文本"},
            {"key": "value", "label": "默认值", "type": "text_input", "default": ""},
            {"key": "placeholder", "label": "占位符", "type": "text_input", "default": "在此输入..."},
        ],
    },
    "number_input": {
        "label": "Number Input",
        "params": [
            {"key": "label", "label": "标签", "type": "text_input", "default": "请输入数字"},
            {"key": "value", "label": "默认值", "type": "number_input", "default": 0},
            {"key": "min_value", "label": "最小值", "type": "number_input", "default": 0},
            {"key": "max_value", "label": "最大值", "type": "number_input", "default": 100},
            {"key": "step", "label": "步长", "type": "number_input", "default": 1},
        ],
    },
    "selectbox": {
        "label": "Selectbox",
        "params": [
            {"key": "label", "label": "标签", "type": "text_input", "default": "请选择"},
            {"key": "options_csv", "label": "选项（逗号分隔）", "type": "text_input", "default": "A,B,C"},
            {"key": "index", "label": "默认选中索引", "type": "number_input", "default": 0},
        ],
    },
    "checkbox": {
        "label": "Checkbox",
        "params": [
            {"key": "label", "label": "标签", "type": "text_input", "default": "选项"},
            {"key": "value", "label": "默认选中", "type": "checkbox", "default": False},
        ],
    },
    "slider": {
        "label": "Slider",
        "params": [
            {"key": "label", "label": "标签", "type": "text_input", "default": "滑块"},
            {"key": "min_value", "label": "最小值", "type": "number_input", "default": 0},
            {"key": "max_value", "label": "最大值", "type": "number_input", "default": 100},
            {"key": "value", "label": "默认值", "type": "number_input", "default": 50},
        ],
    },
    "date_input": {
        "label": "Date Input",
        "params": [
            {"key": "label", "label": "标签", "type": "text_input", "default": "选择日期"},
        ],
    },
    "time_input": {
        "label": "Time Input",
        "params": [
            {"key": "label", "label": "标签", "type": "text_input", "default": "选择时间"},
        ],
    },
    "button": {
        "label": "Button",
        "params": [
            {"key": "label", "label": "按钮文本", "type": "text_input", "default": "点击"},
        ],
    },
    "file_uploader": {
        "label": "File Uploader",
        "params": [
            {"key": "label", "label": "标签", "type": "text_input", "default": "上传文件"},
            {"key": "type_csv", "label": "允许类型（逗号分隔）", "type": "text_input", "default": ""},
            {"key": "accept_multiple_files", "label": "允许多文件", "type": "checkbox", "default": False},
        ],
    },
    "image": {
        "label": "Image(URL)",
        "params": [
            {"key": "url", "label": "图片URL", "type": "text_input", "default": "https://placehold.co/600x200/png"},
            {"key": "caption", "label": "说明", "type": "text_input", "default": ""},
            {"key": "use_column_width", "label": "适应列宽", "type": "checkbox", "default": True},
        ],
    },
    # 容器：垂直堆叠
    "container": {
        "label": "容器-垂直",
        "params": [
            {"key": "label", "label": "容器标签（可选）", "type": "text_input", "default": ""},
        ],
    },
    # 容器：分栏布局
    "columns": {
        "label": "容器-分栏",
        "params": [
            {"key": "spec_csv", "label": "列宽（逗号分隔，如 1,2,1）", "type": "text_input", "default": "1,1"},
            {"key": "num_cols", "label": "列数（可选；留空按列宽）", "type": "number_input", "default": 2},
        ],
    },
}


def ensure_state():
    # 以 JSON 作为单一事实来源
    if "doc" not in st.session_state:
        st.session_state.doc = {
            "version": 1,
            "page_title": "无代码页面",
            "components": [],
        }
    # 向后兼容旧的 session_state.components（若存在则合并到 doc 中）
    if "components" in st.session_state and st.session_state.components:
        if not st.session_state.doc.get("components"):
            st.session_state.doc["components"] = st.session_state.components
    if "selected_comp_id" not in st.session_state:
        st.session_state.selected_comp_id = None
    if "json_text" not in st.session_state:
        st.session_state.json_text = json.dumps(st.session_state.doc, ensure_ascii=False, indent=2)


def new_component_id() -> str:
    return str(uuid.uuid4())


def build_component_label(comp: Dict[str, Any]) -> str:
    ctype = comp.get("type", "component")
    label = COMPONENT_DEFS.get(ctype, {}).get("label", ctype)
    # 展示部分关键参数以便识别
    props = comp.get("props", {})
    hint = props.get("label") or props.get("text") or props.get("content") or ""
    if hint:
        return f"{label} · {str(hint)[:20]}"
    return label


def component_palette_form() -> Dict[str, Any]:
    st.subheader("添加组件")
    ctype = st.selectbox("选择组件类型", options=list(COMPONENT_DEFS.keys()), format_func=lambda k: COMPONENT_DEFS[k]["label"])  # type: ignore
    params_def = COMPONENT_DEFS[ctype]["params"]
    props: Dict[str, Any] = {}
    with st.form(key=f"add_form_{ctype}"):
        for p in params_def:
            key = p["key"]
            label = p["label"]
            ptype = p["type"]
            default = p.get("default")
            if ptype == "text_input":
                props[key] = st.text_input(label, value=str(default) if default is not None else "")
            elif ptype == "text_area":
                props[key] = st.text_area(label, value=str(default) if default is not None else "")
            elif ptype == "number_input":
                props[key] = st.number_input(label, value=float(default) if default is not None else 0.0)
            elif ptype == "checkbox":
                props[key] = st.checkbox(label, value=bool(default))
            else:
                props[key] = st.text_input(label, value=str(default) if default is not None else "")
        submitted = st.form_submit_button("添加到页面")
        if submitted:
            # 处理容器类型的 children 初始化
            comp = {"id": new_component_id(), "type": ctype, "props": props}
            if ctype == "container":
                comp["children"] = []
            elif ctype == "columns":
                spec_csv = str(props.get("spec_csv", "")).strip()
                num_cols_val = props.get("num_cols")
                try:
                    num_cols = int(num_cols_val) if num_cols_val is not None else None
                except Exception:
                    num_cols = None
                if spec_csv:
                    spec_list = [s.strip() for s in spec_csv.split(",") if s.strip()]
                    n = len(spec_list)
                else:
                    n = num_cols if (isinstance(num_cols, int) and num_cols > 0) else 2
                comp["children"] = [[] for _ in range(n)]
            st.session_state.doc["components"].append(comp)
            # 同步 JSON 文本视图
            st.session_state.json_text = json.dumps(st.session_state.doc, ensure_ascii=False, indent=2)
            st.success(f"已添加组件：{build_component_label(comp)}")


def reorder_components_ui():
    st.subheader("拖拽排序")
    if not st.session_state.doc["components"]:
        st.info("当前还没有组件，请先在左侧添加组件。")
        return
    # 构造可拖拽列表数据
    data = [
        {"id": comp["id"], "order": i, "name": f"{i+1}. {build_component_label(comp)}"}
        for i, comp in enumerate(st.session_state.doc["components"]) 
    ]
    if DRAGGABLE_AVAILABLE:
        slist = DraggableList(data, width="100%")  # 返回新的顺序
        # 根据返回值进行重排（兼容不同返回结构）
        try:
            # 如果返回带有 id 的列表，则按 id 映射重排
            new_order_ids = [item.get("id") for item in slist if isinstance(item, dict) and item.get("id")]
            if new_order_ids and set(new_order_ids) == {d["id"] for d in data}:
                id_to_comp = {c["id"]: c for c in st.session_state.doc["components"]}
                st.session_state.doc["components"] = [id_to_comp[cid] for cid in new_order_ids]
                st.session_state.json_text = json.dumps(st.session_state.doc, ensure_ascii=False, indent=2)
        except Exception:
            pass
    else:
        st.warning("未检测到拖拽组件库（streamlit-draggable-list）。已降级为上移/下移按钮排序。")
        # 简易排序降级：选择一个组件并上移/下移
        names = [d["name"] for d in data]
        idx = st.selectbox("选择要调整的组件", options=list(range(len(names))), format_func=lambda i: names[i])
        cols = st.columns(2)
        with cols[0]:
            if st.button("上移", use_container_width=True) and idx > 0:
                comps = st.session_state.doc["components"]
                comps[idx-1], comps[idx] = comps[idx], comps[idx-1]
        with cols[1]:
            if st.button("下移", use_container_width=True) and idx < len(st.session_state.doc["components"])-1:
                comps = st.session_state.doc["components"]
                comps[idx+1], comps[idx] = comps[idx], comps[idx+1]
        st.session_state.json_text = json.dumps(st.session_state.doc, ensure_ascii=False, indent=2)


def select_component_for_edit():
    st.subheader("编辑/删除组件")
    if not st.session_state.doc["components"]:
        return
    options = [(comp["id"], build_component_label(comp)) for comp in st.session_state.doc["components"]]
    selected_label_map = {cid: label for cid, label in options}
    selected_id = st.selectbox("选择组件", options=[cid for cid, _ in options], format_func=lambda cid: selected_label_map[cid])
    st.session_state.selected_comp_id = selected_id
    comp = next((c for c in st.session_state.doc["components"] if c["id"] == selected_id), None)
    if not comp:
        return
    params_def = COMPONENT_DEFS.get(comp["type"], {}).get("params", [])
    with st.form(key=f"edit_form_{selected_id}"):
        for p in params_def:
            key = p["key"]
            label = p["label"]
            ptype = p["type"]
            current = comp["props"].get(key, p.get("default"))
            if ptype == "text_input":
                comp["props"][key] = st.text_input(label, value=str(current) if current is not None else "")
            elif ptype == "text_area":
                comp["props"][key] = st.text_area(label, value=str(current) if current is not None else "")
            elif ptype == "number_input":
                # number_input 必须是数字
                try:
                    num_val = float(current) if current is not None else 0.0
                except Exception:
                    num_val = 0.0
                comp["props"][key] = st.number_input(label, value=num_val)
            elif ptype == "checkbox":
                comp["props"][key] = st.checkbox(label, value=bool(current))
            else:
                comp["props"][key] = st.text_input(label, value=str(current) if current is not None else "")
        col1, col2, col3 = st.columns(3)
        with col1:
            save = st.form_submit_button("保存修改")
        with col2:
            delete = st.form_submit_button("删除组件")
        with col3:
            cancel = st.form_submit_button("取消")
        if save:
            st.session_state.json_text = json.dumps(st.session_state.doc, ensure_ascii=False, indent=2)
            st.success("已保存组件参数")
        if delete:
            st.session_state.doc["components"] = [c for c in st.session_state.doc["components"] if c["id"] != selected_id]
            st.session_state.selected_comp_id = None
            st.session_state.json_text = json.dumps(st.session_state.doc, ensure_ascii=False, indent=2)
            st.warning("已删除组件")
        if cancel:
            st.info("已取消修改")

    # 如果是容器，提供添加子组件与子组件排序能力
    if comp.get("type") in ("container", "columns"):
        st.divider()
        st.subheader("容器子组件管理")
        # 添加子组件表单
        with st.form(key=f"add_child_{selected_id}"):
            child_type = st.selectbox("子组件类型", options=list(COMPONENT_DEFS.keys()), format_func=lambda k: COMPONENT_DEFS[k]["label"])  # type: ignore
            child_params_def = COMPONENT_DEFS[child_type]["params"]
            child_props: Dict[str, Any] = {}
            for p in child_params_def:
                key = p["key"]
                label = p["label"]
                ptype = p["type"]
                default = p.get("default")
                if ptype == "text_input":
                    child_props[key] = st.text_input(label, value=str(default) if default is not None else "")
                elif ptype == "text_area":
                    child_props[key] = st.text_area(label, value=str(default) if default is not None else "")
                elif ptype == "number_input":
                    child_props[key] = st.number_input(label, value=float(default) if default is not None else 0.0)
                elif ptype == "checkbox":
                    child_props[key] = st.checkbox(label, value=bool(default))
                else:
                    child_props[key] = st.text_input(label, value=str(default) if default is not None else "")
            # 若为分栏容器，选择目标列
            target_col_idx = None
            if comp.get("type") == "columns":
                ncols = len(comp.get("children", []))
                target_col_idx = st.selectbox("目标列", options=list(range(ncols)), format_func=lambda i: f"列 {i+1}")
            submitted_child = st.form_submit_button("添加子组件到容器")
            if submitted_child:
                child = {"id": new_component_id(), "type": child_type, "props": child_props}
                # 如果子组件本身也是容器，初始化 children
                if child_type == "container":
                    child["children"] = []
                elif child_type == "columns":
                    spec_csv = str(child_props.get("spec_csv", "")).strip()
                    num_cols_val = child_props.get("num_cols")
                    try:
                        num_cols = int(num_cols_val) if num_cols_val is not None else None
                    except Exception:
                        num_cols = None
                    if spec_csv:
                        n = len([s.strip() for s in spec_csv.split(",") if s.strip()])
                    else:
                        n = num_cols if (isinstance(num_cols, int) and num_cols > 0) else 2
                    child["children"] = [[] for _ in range(n)]
                if comp.get("type") == "columns" and target_col_idx is not None:
                    comp["children"][int(target_col_idx)].append(child)
                else:
                    comp.setdefault("children", []).append(child)
                st.session_state.json_text = json.dumps(st.session_state.doc, ensure_ascii=False, indent=2)
                st.success("已添加子组件到容器")

        # 子组件排序（容器内）
        def _reorder_list(items: List[Dict[str, Any]], label_prefix: str):
            if not items:
                st.info("容器当前没有子组件。")
                return
            data = [{"id": it["id"], "order": i, "name": f"{label_prefix}{i+1}. {build_component_label(it)}"} for i, it in enumerate(items)]
            if DRAGGABLE_AVAILABLE:
                sl = DraggableList(data, width="100%")
                try:
                    new_ids = [d.get("id") for d in sl if isinstance(d, dict) and d.get("id")]
                    if new_ids and set(new_ids) == {d["id"] for d in data}:
                        id_to_item = {i["id"]: i for i in items}
                        items[:] = [id_to_item[iid] for iid in new_ids]
                        st.session_state.json_text = json.dumps(st.session_state.doc, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            else:
                st.warning("拖拽库不可用，使用上/下移动降级方案。")
                names = [d["name"] for d in data]
                idx = st.selectbox("选择子组件", options=list(range(len(names))), format_func=lambda i: names[i])
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("上移") and idx > 0:
                        items[idx-1], items[idx] = items[idx], items[idx-1]
                with c2:
                    if st.button("下移") and idx < len(items)-1:
                        items[idx+1], items[idx] = items[idx], items[idx+1]
                st.session_state.json_text = json.dumps(st.session_state.doc, ensure_ascii=False, indent=2)

        if comp.get("type") == "container":
            _reorder_list(comp.get("children", []), label_prefix="子")
        elif comp.get("type") == "columns":
            ncols = len(comp.get("children", []))
            col_choice = st.selectbox("选择列进行排序", options=list(range(ncols)), format_func=lambda i: f"列 {i+1}")
            _reorder_list(comp.get("children", [[]])[int(col_choice)], label_prefix=f"列{int(col_choice)+1}-子")


def render_component(comp: Dict[str, Any], preview: bool = False):
    ctype = comp.get("type")
    props = comp.get("props", {})
    try:
        if ctype == "markdown":
            st.markdown(props.get("content", ""))
        elif ctype == "header":
            st.header(props.get("text", ""))
        elif ctype == "subheader":
            st.subheader(props.get("text", ""))
        elif ctype == "text":
            st.text(props.get("text", ""))
        elif ctype == "divider":
            st.divider()
        elif ctype == "text_input":
            st.text_input(props.get("label", ""), value=props.get("value", ""), placeholder=props.get("placeholder", ""))
        elif ctype == "number_input":
            st.number_input(
                props.get("label", ""),
                value=float(props.get("value", 0)),
                min_value=float(props.get("min_value", 0)),
                max_value=float(props.get("max_value", 100)),
                step=float(props.get("step", 1)),
            )
        elif ctype == "selectbox":
            options_csv = str(props.get("options_csv", "A,B,C"))
            options = [o.strip() for o in options_csv.split(",") if o.strip()]
            index = int(props.get("index", 0)) if options else 0
            if index < 0 or index >= len(options):
                index = 0
            st.selectbox(props.get("label", ""), options=options, index=index)
        elif ctype == "checkbox":
            st.checkbox(props.get("label", ""), value=bool(props.get("value", False)))
        elif ctype == "slider":
            st.slider(
                props.get("label", ""),
                min_value=float(props.get("min_value", 0)),
                max_value=float(props.get("max_value", 100)),
                value=float(props.get("value", 50)),
            )
        elif ctype == "date_input":
            st.date_input(props.get("label", "日期"))
        elif ctype == "time_input":
            st.time_input(props.get("label", "时间"))
        elif ctype == "button":
            st.button(props.get("label", "按钮"))
        elif ctype == "file_uploader":
            type_csv = props.get("type_csv", "")
            types = [t.strip() for t in str(type_csv).split(",") if t.strip()]
            st.file_uploader(props.get("label", "上传文件"), type=types if types else None, accept_multiple_files=bool(props.get("accept_multiple_files", False)))
        elif ctype == "image":
            st.image(props.get("url", ""), caption=props.get("caption", ""), use_column_width=bool(props.get("use_column_width", True)))
        else:
            st.warning(f"未知组件类型：{ctype}")
    except Exception as e:
        st.error(f"渲染组件出错：{e}")


def render_node(node: Dict[str, Any], preview: bool = False):
    ntype = node.get("type")
    # 容器处理
    if ntype == "container":
        children = node.get("children", [])
        for ch in children:
            render_node(ch, preview=preview)
        return
    if ntype == "columns":
        props = node.get("props", {})
        spec_csv = str(props.get("spec_csv", "")).strip()
        children_cols = node.get("children", [])
        # 解析列宽或列数
        spec: List[float] = []
        if spec_csv:
            try:
                spec = [float(s.strip()) for s in spec_csv.split(",") if s.strip()]
            except Exception:
                spec = []
        if not spec:
            spec = [1.0] * max(1, len(children_cols) or int(props.get("num_cols", 2)))
        cols = st.columns(spec)
        # 每列渲染各自的 children（列表）
        for i, col in enumerate(cols):
            with col:
                col_children = children_cols[i] if i < len(children_cols) else []
                for ch in col_children:
                    render_node(ch, preview=preview)
        return
    # 叶子组件
    render_component(node, preview=preview)


def render_page(title: str, editable: bool):
    st.title(title)
    for comp in st.session_state.doc["components"]:
        render_node(comp, preview=not editable)


def page_editor():
    st.title("编辑页面")
    cols = st.columns([1, 1])
    with cols[0]:
        component_palette_form()
    with cols[1]:
        reorder_components_ui()
        select_component_for_edit()
    # JSON 结构编辑/导出
    st.divider()
    st.subheader("JSON 结构")
    with st.expander("查看/编辑 JSON", expanded=False):
        st.caption("组件布局和结构以 JSON 存储。可在此编辑并应用。")
        st.text_area("JSON", key="json_text", height=260)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("应用 JSON", use_container_width=True):
                try:
                    new_doc = json.loads(st.session_state.json_text)
                    # 基础校验
                    if not isinstance(new_doc, dict) or "components" not in new_doc:
                        st.error("JSON 需为对象且包含 components 字段。")
                    else:
                        st.session_state.doc = new_doc
                        st.success("已应用 JSON 到页面。")
                except Exception as e:
                    st.error(f"解析 JSON 失败：{e}")
        with c2:
            if st.button("刷新当前文档到编辑器", use_container_width=True):
                st.session_state.json_text = json.dumps(st.session_state.doc, ensure_ascii=False, indent=2)
        with c3:
            st.download_button("下载 JSON", data=json.dumps(st.session_state.doc, ensure_ascii=False, indent=2), file_name="layout.json", mime="application/json", use_container_width=True)
    # 实时预览区域
    st.divider()
    st.subheader("实时预览")
    for comp in st.session_state.doc["components"]:
        render_node(comp, preview=True)


def generate_code_from_doc(doc: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Auto-generated from JSON layout (supports containers and columns)")
    lines.append("def render(st):")
    def emit_leaf(ctype: str, props: Dict[str, Any], indent: str):
        if ctype == "markdown":
            lines.append(f"{indent}st.markdown({repr(props.get('content', ''))})")
        elif ctype == "header":
            lines.append(f"{indent}st.header({repr(props.get('text', ''))})")
        elif ctype == "subheader":
            lines.append(f"{indent}st.subheader({repr(props.get('text', ''))})")
        elif ctype == "text":
            lines.append(f"{indent}st.text({repr(props.get('text', ''))})")
        elif ctype == "divider":
            lines.append(f"{indent}st.divider()")
        elif ctype == "text_input":
            lines.append(f"{indent}st.text_input({repr(props.get('label', ''))}, value={repr(props.get('value', ''))}, placeholder={repr(props.get('placeholder', ''))})")
        elif ctype == "number_input":
            def _f(x, d):
                try:
                    return float(x)
                except Exception:
                    return d
            val = _f(props.get('value', 0), 0.0)
            min_v = _f(props.get('min_value', 0), 0.0)
            max_v = _f(props.get('max_value', 100), 100.0)
            step_v = _f(props.get('step', 1), 1.0)
            lines.append(f"{indent}st.number_input({repr(props.get('label', ''))}, value={repr(val)}, min_value={repr(min_v)}, max_value={repr(max_v)}, step={repr(step_v)})")
        elif ctype == "selectbox":
            options_csv = str(props.get("options_csv", "A,B,C"))
            options = [o.strip() for o in options_csv.split(",") if o.strip()]
            idx = int(props.get("index", 0)) if options else 0
            if idx < 0 or idx >= len(options):
                idx = 0
            lines.append(f"{indent}st.selectbox({repr(props.get('label',''))}, options={repr(options)}, index={idx})")
        elif ctype == "checkbox":
            lines.append(f"{indent}st.checkbox({repr(props.get('label',''))}, value={repr(bool(props.get('value', False)))})")
        elif ctype == "slider":
            def _f(x, d):
                try:
                    return float(x)
                except Exception:
                    return d
            min_v = _f(props.get('min_value', 0), 0.0)
            max_v = _f(props.get('max_value', 100), 100.0)
            val = _f(props.get('value', 50), 50.0)
            lines.append(f"{indent}st.slider({repr(props.get('label',''))}, min_value={repr(min_v)}, max_value={repr(max_v)}, value={repr(val)})")
        elif ctype == "date_input":
            lines.append(f"{indent}st.date_input({repr(props.get('label','日期'))})")
        elif ctype == "time_input":
            lines.append(f"{indent}st.time_input({repr(props.get('label','时间'))})")
        elif ctype == "button":
            lines.append(f"{indent}st.button({repr(props.get('label','按钮'))})")
        elif ctype == "file_uploader":
            type_csv = props.get("type_csv", "")
            types = [t.strip() for t in str(type_csv).split(",") if t.strip()]
            types_val = repr(types if types else None)
            lines.append(f"{indent}st.file_uploader({repr(props.get('label','上传文件'))}, type={types_val}, accept_multiple_files={repr(bool(props.get('accept_multiple_files', False)))})")
        elif ctype == "image":
            lines.append(f"{indent}st.image({repr(props.get('url',''))}, caption={repr(props.get('caption',''))}, use_column_width={repr(bool(props.get('use_column_width', True)))})")
        else:
            lines.append(f"{indent}st.warning({repr('未知组件类型：' + str(ctype))})")

    def emit_node(node: Dict[str, Any], indent: str):
        ctype = node.get("type")
        if ctype == "container":
            for ch in node.get("children", []):
                emit_node(ch, indent)
            return
        if ctype == "columns":
            props = node.get("props", {})
            spec_csv = str(props.get("spec_csv", "")).strip()
            children_cols = node.get("children", [])
            spec: List[float] = []
            if spec_csv:
                try:
                    spec = [float(s.strip()) for s in spec_csv.split(",") if s.strip()]
                except Exception:
                    spec = []
            if not spec:
                spec = [1.0] * max(1, len(children_cols) or int(props.get("num_cols", 2)))
            lines.append(f"{indent}cols = st.columns({repr(spec)})")
            for i, col_children in enumerate(children_cols):
                lines.append(f"{indent}with cols[{i}]:")
                for ch in col_children:
                    emit_node(ch, indent + "    ")
            return
        # 叶子组件
        emit_leaf(ctype, node.get("props", {}), indent)

    indent0 = "    "
    for comp in doc.get("components", []):
        emit_node(comp, indent0)
    return "\n".join(lines)


def page_preview():
    st.title("预览页面")
    code = generate_code_from_doc(st.session_state.doc)
    with st.expander("生成的代码", expanded=False):
        st.code(code, language="python")
    # 执行生成的代码
    ns: Dict[str, Any] = {"st": st}
    try:
        exec(code, ns)
        render_fn = ns.get("render")
        if callable(render_fn):
            render_fn(st)
        else:
            st.error("生成代码中未找到 render(st) 函数。")
    except Exception as e:
        st.error(f"执行生成代码出错：{e}")


def page_display():
    # 展示页面与预览页面一致，直接执行生成的代码
    st.title("展示页面")
    code = generate_code_from_doc(st.session_state.doc)
    ns: Dict[str, Any] = {"st": st}
    try:
        exec(code, ns)
        render_fn = ns.get("render")
        if callable(render_fn):
            render_fn(st)
        else:
            st.error("生成代码中未找到 render(st) 函数。")
    except Exception as e:
        st.error(f"执行生成代码出错：{e}")


def main():
    ensure_state()
    st.set_page_config(page_title="Streamlit 无代码前端编辑器", layout="wide")
    st.sidebar.success("选择页面进行操作")
    page = st.sidebar.radio("页面", options=["编辑", "预览", "展示"], index=0)
    st.sidebar.info("拖拽排序依赖 streamlit-draggable-list；布局存储为 JSON；预览将自动生成并执行代码。")
    if page == "编辑":
        page_editor()
    elif page == "预览":
        page_preview()
    else:
        page_display()


if __name__ == "__main__":
    main()