import os
import sys
import subprocess


def main():
    # 通过子进程调用 `streamlit run`，与当前 Python 进程隔离，避免重复 Runtime
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "test.py",
        "--server.headless=true",
        "--server.port",
        os.environ.get("ST_TEST_PORT", "8503"),
    ]
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()