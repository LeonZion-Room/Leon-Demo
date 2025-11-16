import os
import threading
import time
import uvicorn
import subprocess
import sys
from utils import load_config

def start_api():
    cfg = load_config()
    host_cfg = cfg.get("host", "auto")
    host = "0.0.0.0" if host_cfg == "auto" else host_cfg
    port = int(cfg.get("api_port", 8000))
    uvicorn.run("file_server:app", host=host, port=port, log_level="info")

def start_streamlit():
    cfg = load_config()
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    host_cfg = cfg.get("host", "auto")
    host = "0.0.0.0" if host_cfg == "auto" else host_cfg
    port = str(cfg.get("ui_port", 8501))
    subprocess.call([sys.executable, "-m", "streamlit", "run", app_path, "--server.address", host, "--server.port", port])

def main():
    t = threading.Thread(target=start_api, daemon=True)
    t.start()
    time.sleep(0.5)
    start_streamlit()

if __name__ == "__main__":
    main()