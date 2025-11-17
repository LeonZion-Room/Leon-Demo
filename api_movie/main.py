import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Optional, Tuple

from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, Header
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import subprocess
import imageio_ffmpeg
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ORIG_DIR = os.path.join(DATA_DIR, "original")
COMP_DIR = os.path.join(DATA_DIR, "compressed")
TMP_DIR = os.path.join(DATA_DIR, "tmp")
PREVIEW_DIR = os.path.join(DATA_DIR, "tmp_preview")
DB_PATH = os.path.join(DATA_DIR, "videos.json")

# 密码配置
CORRECT_PASSWORD = "wswwsw1234"

os.makedirs(ORIG_DIR, exist_ok=True)
os.makedirs(COMP_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def ffmpeg_path() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()

def run_ffmpeg(args: list) -> None:
    p = subprocess.run([ffmpeg_path(), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode("utf-8", errors="ignore"))

def probe_duration(path: str) -> float:
    p = subprocess.run([ffmpeg_path(), "-hide_banner", "-i", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    s = p.stderr.decode("utf-8", errors="ignore")
    for line in s.splitlines():
        if "Duration:" in line:
            part = line.strip().split("Duration:")[1].split(",")[0].strip()
            h, m, sec = part.split(":")
            return int(h) * 3600 + int(m) * 60 + float(sec)
    return 0.0

def fmt_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(n)
    idx = 0
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024.0
        idx += 1
    return ("{:.2f} {}".format(size, units[idx]) if idx > 0 else "{} {}".format(int(size), units[idx]))

def fmt_duration(seconds: float) -> str:
    total = int(round(seconds))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def ensure_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)

def read_db():
    ensure_db()
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def write_db(items):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def save_upload_to(path: str, file: UploadFile):
    with open(path, "wb") as f:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

def compress_video(in_path: str, out_path: str, crf: int):
    run_ffmpeg(["-y", "-i", in_path, "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-c:a", "aac", "-movflags", "+faststart", out_path])

def create_preview(in_path: str, out_path: str, crf: int, duration: int = 15):
    run_ffmpeg(["-y", "-i", in_path, "-t", str(duration), "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-c:a", "aac", "-movflags", "+faststart", out_path])

def build_item(id_: str, name: str, crf: int, orig_path: str, comp_path: str, dur_orig: float, dur_comp: float):
    return {
        "id": id_,
        "name": name,
        "crf": crf,
        "original_path": orig_path,
        "compressed_path": comp_path,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
        "size_original": os.path.getsize(orig_path) if os.path.exists(orig_path) else 0,
        "size_compressed": os.path.getsize(comp_path) if os.path.exists(comp_path) else 0,
        "duration_original": dur_orig,
        "duration_compressed": dur_comp,
    }

def parse_range(range_header: Optional[str], file_size: int) -> Tuple[int, int]:
    if not range_header or not range_header.startswith("bytes="):
        return 0, file_size - 1
    rng = range_header.split("=")[1]
    s, e = rng.split("-") if "-" in rng else (rng, "")
    start = int(s) if s else 0
    end = int(e) if e else file_size - 1
    if start > end:
        start = 0
        end = file_size - 1
    if end >= file_size:
        end = file_size - 1
    return start, end

def streamer(path: str, range_header: Optional[str]):
    if not os.path.exists(path):
        raise HTTPException(status_code=404)
    file_size = os.path.getsize(path)
    start, end = parse_range(range_header, file_size)
    chunk_size = 1024 * 1024
    def gen():
        with open(path, "rb") as f:
            f.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                read_size = min(chunk_size, remaining)
                data = f.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data
    status_code = 206 if range_header else 200
    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
    }
    return StreamingResponse(gen(), media_type="video/mp4", status_code=status_code, headers=headers)

# 主页路由
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# preview路由 - 需要密码验证
@app.post("/preview")
async def preview(request: Request, authorization: str = Header(None), file: UploadFile = File(...), crf: int = Form(...)):
    # 验证密码
    if not authorization or authorization != f"Bearer {CORRECT_PASSWORD}":
        raise HTTPException(status_code=401, detail="未授权访问，请提供正确的密码")
    temp_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1].lower() or ".mp4"
    tmp_path = os.path.join(TMP_DIR, temp_id + ext)
    save_upload_to(tmp_path, file)
    prev_path = os.path.join(PREVIEW_DIR, temp_id + ".mp4")
    create_preview(tmp_path, prev_path, crf)
    return {"temp_id": temp_id, "preview_url": f"/preview/{temp_id}", "name": file.filename, "crf": crf}

@app.get("/preview/{temp_id}")
async def get_preview(request: Request, temp_id: str):
    path = os.path.join(PREVIEW_DIR, temp_id + ".mp4")
    range_h = request.headers.get("range")
    return streamer(path, range_h)

# commit路由 - 需要密码验证
@app.post("/commit")
async def commit(request: Request, authorization: str = Header(None), temp_id: str = Form(...), crf: int = Form(...), title: Optional[str] = Form(None)):
    # 验证密码
    if not authorization or authorization != f"Bearer {CORRECT_PASSWORD}":
        raise HTTPException(status_code=401, detail="未授权访问，请提供正确的密码")
    tmp_candidates = [p for p in os.listdir(TMP_DIR) if p.startswith(temp_id)]
    if not tmp_candidates:
        raise HTTPException(status_code=404, detail="temp not found")
    tmp_name = tmp_candidates[0]
    tmp_path = os.path.join(TMP_DIR, tmp_name)
    new_id = str(uuid.uuid4())
    ext = os.path.splitext(tmp_name)[1].lower()
    orig_path = os.path.join(ORIG_DIR, new_id + ext)
    shutil.move(tmp_path, orig_path)
    comp_path = os.path.join(COMP_DIR, new_id + ".mp4")
    dur_orig = probe_duration(orig_path)
    compress_video(orig_path, comp_path, crf)
    dur_comp = probe_duration(comp_path)
    prev_path = os.path.join(PREVIEW_DIR, temp_id + ".mp4")
    if os.path.exists(prev_path):
        os.remove(prev_path)
    items = read_db()
    items.append(build_item(new_id, title or tmp_name, crf, orig_path, comp_path, dur_orig, dur_comp))
    write_db(items)
    return {"id": new_id}

# upload路由 - 需要密码验证
@app.post("/upload")
async def upload(request: Request, authorization: str = Header(None), file: UploadFile = File(...), crf: int = Form(...), title: Optional[str] = Form(None)):
    # 验证密码
    if not authorization or authorization != f"Bearer {CORRECT_PASSWORD}":
        raise HTTPException(status_code=401, detail="未授权访问，请提供正确的密码")
    new_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1].lower() or ".mp4"
    orig_path = os.path.join(ORIG_DIR, new_id + ext)
    save_upload_to(orig_path, file)
    comp_path = os.path.join(COMP_DIR, new_id + ".mp4")
    dur_orig = probe_duration(orig_path)
    compress_video(orig_path, comp_path, crf)
    dur_comp = probe_duration(comp_path)
    items = read_db()
    items.append(build_item(new_id, title or file.filename, crf, orig_path, comp_path, dur_orig, dur_comp))
    write_db(items)
    return {"id": new_id}

# videos路由 - 获取所有视频列表
@app.get("/videos")
async def videos(request: Request):
    items = read_db()
    def to_wire(x):
        return {
            "id": x["id"],
            "name": x["name"],
            "crf": x["crf"],
            "uploaded_at": x["uploaded_at"],
            "size_original": x["size_original"],
            "size_compressed": x["size_compressed"],
            "size_original_human": fmt_bytes(x["size_original"]),
            "size_compressed_human": fmt_bytes(x["size_compressed"]),
            "duration_original": x.get("duration_original", 0),
            "duration_compressed": x.get("duration_compressed", 0),
            "duration_original_human": fmt_duration(x.get("duration_original", 0)),
            "duration_compressed_human": fmt_duration(x.get("duration_compressed", 0)),
            "original_url": f"/stream/original/{x['id']}",
            "compressed_url": f"/stream/compressed/{x['id']}",
            "view_original_url": f"/view/original/{x['id']}",
            "view_compressed_url": f"/view/compressed/{x['id']}",
        }
    return [to_wire(i) for i in items]

def find_item(id_: str):
    items = read_db()
    for i in items:
        if i["id"] == id_:
            return i
    return None

# stream_original路由 - 流媒体播放原始视频
@app.get("/stream/original/{id}")
async def stream_original(request: Request, id: str):
    item = find_item(id)
    if not item:
        raise HTTPException(status_code=404)
    path = item["original_path"]
    range_h = request.headers.get("range")
    return streamer(path, range_h)

# view_original路由 - 全屏播放原始视频
@app.get("/view/original/{id}", response_class=HTMLResponse)
async def view_original(request: Request, id: str):
    item = find_item(id)
    if not item:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("view.html", {"request": request, "src": f"/stream/original/{id}", "title": item["name"] + " 原始"})

# view_compressed路由 - 全屏播放压缩视频
@app.get("/view/compressed/{id}", response_class=HTMLResponse)
async def view_compressed(request: Request, id: str):
    item = find_item(id)
    if not item:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("view.html", {"request": request, "src": f"/stream/compressed/{id}", "title": item["name"] + " 压缩"})

# stream_compressed路由 - 流媒体播放压缩视频
@app.get("/stream/compressed/{id}")
async def stream_compressed(request: Request, id: str):
    item = find_item(id)
    if not item:
        raise HTTPException(status_code=404)
    path = item["compressed_path"]
    range_h = request.headers.get("range")
    return streamer(path, range_h)

# delete路由 - 删除视频（需要密码验证）
@app.delete("/videos/{id}")
async def delete_video(request: Request, id: str, authorization: str = Header(None)):
    # 验证密码
    if not authorization or authorization != f"Bearer {CORRECT_PASSWORD}":
        raise HTTPException(status_code=401, detail="未授权访问，请提供正确的密码")
    
    item = find_item(id)
    if not item:
        raise HTTPException(status_code=404, detail="视频未找到")
    
    # 从数据库中删除记录
    items = read_db()
    items = [i for i in items if i["id"] != id]
    write_db(items)
    
    # 删除文件系统中的文件
    if os.path.exists(item["original_path"]):
        os.remove(item["original_path"])
    if os.path.exists(item["compressed_path"]):
        os.remove(item["compressed_path"])
    
    return {"message": "视频删除成功"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
