import os
import io
import zipfile
from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from utils import STORAGE_DIR, load_batches

app = FastAPI()

@app.get("/")
def root():
    return PlainTextResponse("FileBox Download Service")

@app.get("/download/{batch_id}/{safe_name}")
def download(batch_id: str, safe_name: str):
    path = os.path.join(STORAGE_DIR, f"batch_{batch_id}", safe_name)
    if not os.path.exists(path):
        return PlainTextResponse("Not Found", status_code=404)
    return FileResponse(path, filename=safe_name)

@app.get("/download_all/{batch_id}")
def download_all(batch_id: str):
    batches = load_batches()
    if batch_id not in batches:
        return PlainTextResponse("Not Found", status_code=404)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for e in batches[batch_id]:
            p = e.get("path")
            n = e.get("safe_name")
            if p and os.path.exists(p):
                zf.write(p, arcname=n)
    buf.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="batch_{batch_id}.zip"'}
    return StreamingResponse(buf, media_type="application/zip", headers=headers)