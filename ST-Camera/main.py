import sys
from streamlit.web import cli as stcli


if __name__ == "__main__":
    # 以脚本方式启动 Streamlit，满足用 `.venv\Scripts\python main.py` 运行的需求
    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        "--server.headless=true",
    ]
    stcli.main()