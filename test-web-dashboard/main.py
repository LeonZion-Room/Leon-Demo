import os
import json
import time
import threading
import uuid
from pathlib import Path
from datetime import datetime
import streamlit as st
import cv2
import numpy as np
from test import capture_screenshot
import io
import zipfile
import pandas as pd

DATA_DIR = Path("data")
BASELINES_DIR = DATA_DIR / "baselines"
RECORDS_DIR = DATA_DIR / "records"
TEMP_DIR = DATA_DIR / "temp"
for p in [DATA_DIR, BASELINES_DIR, RECORDS_DIR, TEMP_DIR]:
    p.mkdir(parents=True, exist_ok=True)
TASKS_JSON = DATA_DIR / "tasks.json"
SIMILARITY_THRESHOLD = 0.9
TASK_LOCK = threading.Lock()

def load_tasks():
    if TASKS_JSON.exists():
        with TASK_LOCK:
            try:
                with open(TASKS_JSON, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"tasks": []}
    return {"tasks": []}

def save_tasks(data):
    with TASK_LOCK:
        with open(TASKS_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def compute_similarity(a_path, b_path):
    a = cv2.imread(str(a_path))
    b = cv2.imread(str(b_path))
    if a is None or b is None:
        return 0.0
    if a.shape != b.shape:
        h = min(a.shape[0], b.shape[0])
        w = min(a.shape[1], b.shape[1])
        a = cv2.resize(a, (w, h))
        b = cv2.resize(b, (w, h))
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    gb = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    ga = cv2.GaussianBlur(ga, (5, 5), 0)
    gb = cv2.GaussianBlur(gb, (5, 5), 0)
    diff = cv2.absdiff(ga, gb)
    _, th = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    changed = np.count_nonzero(th)
    total = th.size
    sim = 1.0 - (changed / total)
    if sim < 0:
        sim = 0.0
    if sim > 1:
        sim = 1.0
    return float(sim)

_scheduler_started = False

def scheduler_worker():
    while True:
        data = load_tasks()
        now = time.time()
        changed = False
        for t in data["tasks"]:
            if not t.get("interval_seconds"):
                continue
            if t.get("is_active", True) is False:
                continue
            nxt = t.get("next_run_ts")
            if nxt is None:
                t["next_run_ts"] = now + int(t["interval_seconds"])
                changed = True
                continue
            if now >= float(nxt):
                ts = int(now)
                outdir = RECORDS_DIR / t["id"]
                outdir.mkdir(parents=True, exist_ok=True)
                shot_path = outdir / f"{ts}.png"
                try:
                    ws = int(t.get("wait_seconds", 3))
                    capture_screenshot(t["url"], str(shot_path), wait_seconds=ws)
                    sim = compute_similarity(Path(t["baseline_path"]), shot_path)
                    ok = sim >= SIMILARITY_THRESHOLD
                    if "records" not in t:
                        t["records"] = []
                    t["records"].append({"ts": ts, "screenshot_path": str(shot_path), "similarity": sim, "is_ok": ok})
                except Exception as e:
                    if "records" not in t:
                        t["records"] = []
                    t["records"].append({"ts": ts, "screenshot_path": str(shot_path), "similarity": 0.0, "is_ok": False, "error": str(e)})
                t["next_run_ts"] = now + int(t["interval_seconds"])
                changed = True
        if changed:
            save_tasks(data)
        time.sleep(1)

def ensure_scheduler():
    global _scheduler_started
    if not _scheduler_started:
        th = threading.Thread(target=scheduler_worker, daemon=True)
        th.start()
        _scheduler_started = True

def render_create_task_page():
    st.header("创建检测任务")
    url = st.text_input("网页URL")
    interval = st.number_input("检测间隔秒", min_value=10, value=300, step=10)
    wait_seconds = st.number_input("截图等待秒", min_value=0, value=3, step=1)
    tags_input = st.text_input("标签（逗号分隔）", value="")
    remark_input = st.text_area("备注", value="", height=80)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("获取基准截图"):
            if url:
                preview_path = TEMP_DIR / f"baseline_{int(time.time())}.png"
                try:
                    capture_screenshot(url, str(preview_path), wait_seconds=int(wait_seconds))
                    st.session_state["baseline_preview_path"] = str(preview_path)
                    st.session_state["create_url"] = url
                    st.session_state["create_interval"] = int(interval)
                    st.session_state["create_wait"] = int(wait_seconds)
                    st.success("已获取基准截图")
                    st.image(str(preview_path))
                except Exception as e:
                    st.error(str(e))
            else:
                st.error("请输入URL")
    with col2:
        if st.button("确认创建检测单元"):
            bp = st.session_state.get("baseline_preview_path")
            cu = st.session_state.get("create_url")
            iv = st.session_state.get("create_interval")
            wt = st.session_state.get("create_wait")
            if bp and cu and iv is not None and wt is not None:
                tid = uuid.uuid4().hex[:8]
                baseline_path = BASELINES_DIR / f"{tid}.png"
                os.replace(bp, baseline_path)
                data = load_tasks()
                now = time.time()
                tags_list = [x.strip() for x in str(tags_input).split(",") if x.strip()]
                task = {
                    "id": tid,
                    "url": cu,
                    "interval_seconds": int(iv),
                    "wait_seconds": int(wt),
                    "baseline_path": str(baseline_path),
                    "created_at": int(now),
                    "next_run_ts": now + int(iv),
                    "is_active": True,
                    "tags": tags_list,
                    "remark": str(remark_input or ""),
                    "records": []
                }
                data["tasks"].append(task)
                save_tasks(data)
                st.session_state.pop("baseline_preview_path", None)
                st.session_state.pop("create_url", None)
                st.session_state.pop("create_interval", None)
                st.session_state.pop("create_wait", None)
                st.success("已创建检测单元")
            else:
                st.error("请先获取并确认基准截图")
    bp = st.session_state.get("baseline_preview_path")
    if bp and os.path.exists(bp):
        st.subheader("基准截图预览")
        st.image(bp)

def render_config_page():
    st.header("配置参数")
    data = load_tasks()
    tasks = data["tasks"]
    if not tasks:
        st.info("暂无任务")
        return
    for t in tasks:
        with st.expander(f"{t['id']} - {t['url']}", expanded=False):
            new_url = st.text_input(f"URL_{t['id']}", value=t["url"], key=f"url_{t['id']}")
            new_iv = st.number_input(f"检测间隔秒_{t['id']}", min_value=10, value=int(t["interval_seconds"]), step=10, key=f"iv_cfg_{t['id']}")
            new_ws = st.number_input(f"截图等待秒_{t['id']}", min_value=0, value=int(t.get("wait_seconds", 3)), step=1, key=f"ws_cfg_{t['id']}")
            new_tags_str = st.text_input(f"标签（逗号分隔）_{t['id']}", value=",".join(t.get("tags", [])), key=f"tags_cfg_{t['id']}")
            new_remark = st.text_area(f"备注_{t['id']}", value=t.get("remark", ""), height=80, key=f"remark_cfg_{t['id']}")
            cols = st.columns(2)
            with cols[0]:
                if st.button(f"保存_{t['id']}", key=f"save_cfg_{t['id']}"):
                    t["url"] = new_url
                    t["interval_seconds"] = int(new_iv)
                    t["wait_seconds"] = int(new_ws)
                    t["tags"] = [x.strip() for x in str(new_tags_str).split(",") if x.strip()]
                    t["remark"] = str(new_remark or "")
                    t["next_run_ts"] = time.time() + int(new_iv)
                    save_tasks(data)
                    st.success("已保存配置")
            with cols[1]:
                st.write("")

def _build_records_zip(task):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        recs = task.get("records", [])
        z.writestr("records.json", json.dumps(recs, ensure_ascii=False, indent=2))
        for r in recs:
            p = r.get("screenshot_path")
            if p and os.path.exists(p):
                arc = f"images/{os.path.basename(p)}"
                z.write(p, arcname=arc)
        bp = task.get("baseline_path")
        if bp and os.path.exists(bp):
            z.write(bp, arcname=f"baseline/{os.path.basename(bp)}")
    buf.seek(0)
    return buf

def render_run_page():
    st.header("启动任务与结果")
    data = load_tasks()
    tasks = data["tasks"]
    if not tasks:
        st.info("暂无任务")
        return
    for t in tasks:
        with st.expander(f"{t['id']} - {t['url']}", expanded=False):
            cols_top = st.columns(3)
            with cols_top[0]:
                if st.button(f"立即检测_{t['id']}", key=f"run_now_{t['id']}"):
                    ts = int(time.time())
                    outdir = RECORDS_DIR / t["id"]
                    outdir.mkdir(parents=True, exist_ok=True)
                    shot_path = outdir / f"{ts}.png"
                    try:
                        ws = int(t.get("wait_seconds", 3))
                        capture_screenshot(t["url"], str(shot_path), wait_seconds=ws)
                        sim = compute_similarity(Path(t["baseline_path"]), shot_path)
                        ok = sim >= SIMILARITY_THRESHOLD
                        if "records" not in t:
                            t["records"] = []
                        t["records"].append({"ts": ts, "screenshot_path": str(shot_path), "similarity": sim, "is_ok": ok})
                        save_tasks(data)
                        st.success("已执行检测")
                    except Exception as e:
                        st.error(str(e))
            with cols_top[1]:
                st.write("")
            with cols_top[2]:
                zip_buf = _build_records_zip(t)
                st.download_button(label=f"下载全部记录_{t['id']}", data=zip_buf, file_name=f"records_{t['id']}.zip", key=f"dl_{t['id']}")

            recs = sorted(t.get("records", []), key=lambda x: x["ts"], reverse=True)[:3]

def _task_status(t):
    recs = t.get("records", [])
    last = recs[-1] if recs else None
    status = "运行中" if t.get("is_active", True) else "已暂停"
    last_time = format_ts(last["ts"]) if last else "无"
    last_sim = f"{round(last['similarity']*100,2)}%" if last else "无"
    next_run = format_ts(t["next_run_ts"]) if t.get("next_run_ts") else "无"
    return status, last_time, last_sim, next_run

def render_manage_page():
    st.header("任务管理")
    data = load_tasks()
    tasks = data["tasks"]
    if not tasks:
        st.info("暂无任务")
        return
    tab_all, tab_running, tab_paused = st.tabs(["全部任务", "运行中", "已暂停"])
    def render_task_cards(ts, prefix):
        for t in ts:
            status, last_time, last_sim, next_run = _task_status(t)
            with st.expander(f"{t['id']} - {t['url']}", expanded=False):
                st.write(f"状态: {status}")
                st.write(f"上次运行时间: {last_time}")
                st.write(f"最近相似度: {last_sim}")
                st.write(f"下次检测: {next_run}")
                cols = st.columns(3)
                with cols[0]:
                    if t.get("is_active", True):
                        if st.button(f"暂停任务_{t['id']}", key=f"{prefix}_pause_{t['id']}"):
                            t["is_active"] = False
                            save_tasks(data)
                            st.success("已暂停")
                    else:
                        if st.button(f"启动任务_{t['id']}", key=f"{prefix}_start_{t['id']}"):
                            t["is_active"] = True
                            t["next_run_ts"] = time.time() + int(t.get("interval_seconds", 300))
                            save_tasks(data)
                            st.success("已启动")
                with cols[1]:
                    st.write("")
                with cols[2]:
                    st.write("")
    with tab_all:
        render_task_cards(tasks, "all")
    with tab_running:
        render_task_cards([t for t in tasks if t.get("is_active", True)], "running")
    with tab_paused:
        render_task_cards([t for t in tasks if not t.get("is_active", True)], "paused")

def render_units_page():
    st.header("所有单元")
    data = load_tasks()
    tasks = data["tasks"]
    if not tasks:
        st.info("暂无任务")
        return
    filt = st.selectbox("筛选", ["全部", "运行中", "已暂停"], index=0, key="units_filter")
    if filt == "运行中":
        tasks_to_show = [t for t in tasks if t.get("is_active", True)]
    elif filt == "已暂停":
        tasks_to_show = [t for t in tasks if not t.get("is_active", True)]
    else:
        tasks_to_show = tasks
    st.metric("当前数量", len(tasks_to_show))

   
    st.divider()
    for t in tasks_to_show:
        with st.container():
            with st.expander(f"{t['id']} - {t['url']}", expanded=False):
                status, last_time, last_sim, next_run = _task_status(t)
                recs = t.get("records", [])
                last = recs[-1] if recs else None
                sim_val = float(last["similarity"]) if last else 0.0
                tags_show = ", ".join(t.get("tags", []))
                if tags_show:
                    st.caption(f"标签: {tags_show}")
                if t.get("remark"):
                    st.info(t.get("remark"))
                if last and last.get("is_ok", False):
                    st.success("单元健康")
                else:
                    st.warning("单元可能异常或暂无记录")
              
                toggle_val = st.toggle("运行状态", value=t.get("is_active", True), key=f"units_tgl_{t['id']}")
                if toggle_val != t.get("is_active", True):
                    t["is_active"] = bool(toggle_val)
                    if toggle_val:
                        t["next_run_ts"] = time.time() + int(t.get("interval_seconds", 300))
                    save_tasks(data)
                    st.success("已更新运行状态")
                cols_actions = st.columns(3)
                with cols_actions[0]:
                    if st.button(f"编辑任务_{t['id']}", key=f"units_edit_{t['id']}"):
                        st.session_state["units_edit_id"] = t["id"]
                with cols_actions[1]:
                    zip_buf = _build_records_zip(t)
                    st.download_button(label=f"下载记录_{t['id']}", data=zip_buf, file_name=f"records_{t['id']}.zip", key=f"units_dl_{t['id']}")
                with cols_actions[2]:
                    if st.button(f"立即检测_{t['id']}", key=f"units_run_{t['id']}"):
                        ts = int(time.time())
                        outdir = RECORDS_DIR / t["id"]
                        outdir.mkdir(parents=True, exist_ok=True)
                        shot_path = outdir / f"{ts}.png"
                        try:
                            ws = int(t.get("wait_seconds", 3))
                            capture_screenshot(t["url"], str(shot_path), wait_seconds=ws)
                            sim = compute_similarity(Path(t["baseline_path"]), shot_path)
                            ok = sim >= SIMILARITY_THRESHOLD
                            if "records" not in t:
                                t["records"] = []
                            t["records"].append({"ts": ts, "screenshot_path": str(shot_path), "similarity": sim, "is_ok": ok})
                            save_tasks(data)
                            st.success("已执行检测")
                        except Exception as e:
                            st.error(str(e))
                recs_compact = sorted(recs, key=lambda x: x["ts"], reverse=True)[:3]
                if recs_compact:
                    df = pd.DataFrame([
                        {"时间": format_ts(r["ts"]), "相似度": f"{round(r['similarity']*100,2)}%", "状态": "正常" if r["is_ok"] else "异常"}
                        for r in recs_compact
                    ])
                    st.dataframe(df, use_container_width=True)
                    cols_imgs = st.columns(len(recs_compact))
                    for i, r in enumerate(recs_compact):
                        with cols_imgs[i]:
                            p = r.get("screenshot_path")
                            if p and os.path.exists(p):
                                st.image(p, caption=f"{format_ts(r['ts'])} | {round(r['similarity']*100,2)}%", use_column_width=True)
            st.divider()

    edit_id = st.session_state.get("units_edit_id")
    if edit_id:
        t = next((x for x in tasks if x["id"] == edit_id), None)
        if t:
            with st.form(f"units_edit_form_{edit_id}"):
                new_url = st.text_input("URL", value=t["url"], key=f"units_edit_url_{edit_id}")
                new_iv = st.number_input("检测间隔秒", min_value=10, value=int(t["interval_seconds"]), step=10, key=f"units_edit_iv_{edit_id}")
                new_ws = st.number_input("截图等待秒", min_value=0, value=int(t.get("wait_seconds", 3)), step=1, key=f"units_edit_ws_{edit_id}")
                new_tags_str = st.text_input("标签（逗号分隔）", value=",".join(t.get("tags", [])), key=f"units_edit_tags_{edit_id}")
                new_remark = st.text_area("备注", value=t.get("remark", ""), height=80, key=f"units_edit_remark_{edit_id}")
                submitted = st.form_submit_button("保存")
                if submitted:
                    t["url"] = new_url
                    t["interval_seconds"] = int(new_iv)
                    t["wait_seconds"] = int(new_ws)
                    t["tags"] = [x.strip() for x in str(new_tags_str).split(",") if x.strip()]
                    t["remark"] = str(new_remark or "")
                    if t.get("is_active", True):
                        t["next_run_ts"] = time.time() + int(new_iv)
                    save_tasks(data)
                    st.session_state.pop("units_edit_id", None)
                    st.success("已保存")
            if st.button("取消", key=f"units_edit_cancel_{edit_id}"):
                st.session_state.pop("units_edit_id", None)

def render_exec_page():
    st.header("执行情况")
    data = load_tasks()
    tasks = [t for t in data["tasks"] if t.get("is_active", True)]
    if not tasks:
        st.info("暂无运行中的任务")
        return
    st.metric("运行中任务数", len(tasks))


            
    for t in tasks:
        with st.container():
            with st.expander(f"{t['id']} - {t['url']}", expanded=False):
                tags_show = ", ".join(t.get("tags", []))
                if tags_show:
                    st.caption(f"标签: {tags_show}")
                if t.get("remark"):
                    st.caption(f"备注: {t.get('remark')}")
                recs = sorted(t.get("records", []), key=lambda x: x["ts"], reverse=True)[:3]
                if not recs:
                    st.write("暂无记录")
                else:
                    last = recs[0]
                    if last.get("is_ok", False):
                        st.success("任务最近状态正常")
                    else:
                        st.warning("任务最近状态异常")
                    act_cols = st.columns(3)
                    with act_cols[0]:
                        if st.button(f"立即检测_{t['id']}", key=f"exec_run_{t['id']}"):
                            ts = int(time.time())
                            outdir = RECORDS_DIR / t["id"]
                            outdir.mkdir(parents=True, exist_ok=True)
                            shot_path = outdir / f"{ts}.png"
                            try:
                                ws = int(t.get("wait_seconds", 3))
                                capture_screenshot(t["url"], str(shot_path), wait_seconds=ws)
                                sim = compute_similarity(Path(t["baseline_path"]), shot_path)
                                ok = sim >= SIMILARITY_THRESHOLD
                                if "records" not in t:
                                    t["records"] = []
                                t["records"].append({"ts": ts, "screenshot_path": str(shot_path), "similarity": sim, "is_ok": ok})
                                save_tasks(data)
                                st.success("已执行检测")
                            except Exception as e:
                                st.error(str(e))
                    with act_cols[1]:
                        zip_buf = _build_records_zip(t)
                        st.download_button(label=f"下载记录_{t['id']}", data=zip_buf, file_name=f"records_{t['id']}.zip", key=f"exec_dl_{t['id']}")
                    with act_cols[2]:
                        st.write("")
                    df = pd.DataFrame([
                        {"时间": format_ts(r["ts"]), "相似度": f"{round(r['similarity'] * 100, 2)}%", "状态": "正常" if r["is_ok"] else "异常"}
                        for r in recs
                    ])
                    st.dataframe(df, use_container_width=True)
                    cols_imgs = st.columns(len(recs))
                    for i, r in enumerate(recs):
                        with cols_imgs[i]:
                            p = r.get("screenshot_path")
                            if p and os.path.exists(p):
                                st.image(p, caption=f"{format_ts(r['ts'])} | {round(r['similarity']*100,2)}%", use_column_width=True)
            st.divider()

def format_ts(ts):
    return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")

def render_tasks_page():
    st.header("检测任务与记录")
    data = load_tasks()
    tasks = data["tasks"]
    if not tasks:
        st.info("暂无任务")
        return
    for t in tasks:
        with st.container():
            st.subheader(t["id"]) 
            st.write(f"URL: {t['url']}")
            st.write(f"间隔: {int(t['interval_seconds'])} 秒")
            st.write(f"截图等待: {int(t.get('wait_seconds', 3))} 秒")
            nxt = t.get("next_run_ts")
            if nxt:
                st.write(f"下次检测: {format_ts(nxt)}")
            colA, colB, colC = st.columns(3)
            with colA:
                new_iv = st.number_input(f"更新间隔秒_{t['id']}", min_value=10, value=int(t["interval_seconds"]), step=10, key=f"iv_{t['id']}")
                if st.button(f"保存间隔_{t['id']}"):
                    t["interval_seconds"] = int(new_iv)
                    t["next_run_ts"] = time.time() + int(new_iv)
                    save_tasks(data)
                    st.success("已更新间隔")
            with colB:
                new_ws = st.number_input(f"更新截图等待秒_{t['id']}", min_value=0, value=int(t.get("wait_seconds", 3)), step=1, key=f"ws_{t['id']}")
                if st.button(f"保存等待_{t['id']}"):
                    t["wait_seconds"] = int(new_ws)
                    save_tasks(data)
                    st.success("已更新等待时间")
            with colC:
                if st.button(f"立即检测_{t['id']}"):
                    ts = int(time.time())
                    outdir = RECORDS_DIR / t["id"]
                    outdir.mkdir(parents=True, exist_ok=True)
                    shot_path = outdir / f"{ts}.png"
                    try:
                        ws = int(t.get("wait_seconds", 3))
                        capture_screenshot(t["url"], str(shot_path), wait_seconds=ws)
                        sim = compute_similarity(Path(t["baseline_path"]), shot_path)
                        ok = sim >= SIMILARITY_THRESHOLD
                        t["records"].append({"ts": ts, "screenshot_path": str(shot_path), "similarity": sim, "is_ok": ok})
                        save_tasks(data)
                        st.success("已执行检测")
                    except Exception as e:
                        st.error(str(e))
            if t.get("records"):
                st.write("最近记录")
                for r in sorted(t["records"], key=lambda x: x["ts"], reverse=True)[:5]:
                    st.write(f"时间: {format_ts(r['ts'])}")
                    st.write(f"相似度: {round(r['similarity'] * 100, 2)}%")
                    st.write("状态: 正常" if r["is_ok"] else "状态: 异常")
                    cols = st.columns(2)
                    with cols[0]:
                        st.image(t["baseline_path"], caption="基准")
                    with cols[1]:
                        st.image(r["screenshot_path"], caption="当前")

def main():
    ensure_scheduler()
    st.set_page_config(page_title="网页状态检测器", layout="wide")
    st.sidebar.title("网页状态检测器")
    page = st.sidebar.selectbox("页面", ["创建任务", "所有单元", "执行情况"])
    if page == "创建任务":
        render_create_task_page()
    elif page == "所有单元":
        render_units_page()
    else:
        render_exec_page()

if __name__ == "__main__":
    if os.environ.get("IS_STREAMLIT_APP") != "1":
        os.environ["IS_STREAMLIT_APP"] = "1"
        from streamlit.web import cli as stcli
        import sys
        sys.argv = ["streamlit", "run", os.path.abspath(__file__)]
        stcli.main()
    else:
        main()
