import os
from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse
from utils import STORAGE_DIR

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