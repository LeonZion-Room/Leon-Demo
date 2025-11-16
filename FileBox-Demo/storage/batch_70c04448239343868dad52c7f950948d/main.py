import os
import threading
import time
import uvicorn
import subprocess
import sys

def start_api():
    uvicorn.run("file_server:app", host="127.0.0.1", port=8000, log_level="info")

def start_streamlit():
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    subprocess.call([sys.executable, "-m", "streamlit", "run", app_path])

def main():
    t = threading.Thread(target=start_api, daemon=True)
    t.start()
    time.sleep(0.5)
    start_streamlit()

if __name__ == "__main__":
    main()