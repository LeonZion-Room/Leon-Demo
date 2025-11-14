from pathlib import Path
import subprocess
import time
from typing import Any
from frp_manager.config import get_binary, generate_ini

def _pid_file(base: Path, type_: str, name: str) -> Path:
    return base / "run" / type_ / name / "proc.pid"

def _log_file(base: Path, type_: str, name: str) -> Path:
    return base / "logs" / type_ / f"{name}.log"

def _is_running(pid: int) -> bool:
    try:
        out = subprocess.check_output(["cmd", "/c", f"tasklist /FI \"PID eq {pid}\""])
        return str(pid) in out.decode("utf-8", errors="ignore")
    except Exception:
        return False

def start_profile(base: Path, type_: str, name: str) -> int:
    b = get_binary(base, type_)
    if b is None or not b.exists():
        raise RuntimeError("binary not configured")
    ini = generate_ini(base, type_, name)
    log = _log_file(base, type_, name)
    log.parent.mkdir(parents=True, exist_ok=True)
    f = open(log, "ab", buffering=0)
    try:
        p = subprocess.Popen([str(b), "-c", str(ini)], stdout=f, stderr=subprocess.STDOUT)
    except Exception:
        f.close()
        raise
    pid = p.pid
    _pid_file(base, type_, name).write_text(str(pid), encoding="utf-8")
    time.sleep(0.5)
    return pid

def stop_profile(base: Path, type_: str, name: str) -> None:
    p = _pid_file(base, type_, name)
    if not p.exists():
        return
    pid = int(p.read_text(encoding="utf-8").strip())
    try:
        subprocess.run(["cmd", "/c", f"taskkill /PID {pid} /F"], check=False)
    finally:
        try:
            p.unlink()
        except Exception:
            pass

def profile_status(base: Path, type_: str, name: str) -> bool:
    p = _pid_file(base, type_, name)
    if not p.exists():
        return False
    try:
        pid = int(p.read_text(encoding="utf-8").strip())
    except Exception:
        return False
    return _is_running(pid)