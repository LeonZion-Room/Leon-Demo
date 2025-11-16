from pathlib import Path
import json
from typing import Any

def ensure_base(base: Path) -> None:
    (base / "configs" / "client").mkdir(parents=True, exist_ok=True)
    (base / "configs" / "server").mkdir(parents=True, exist_ok=True)
    (base / "run" / "client").mkdir(parents=True, exist_ok=True)
    (base / "run" / "server").mkdir(parents=True, exist_ok=True)
    (base / "logs" / "client").mkdir(parents=True, exist_ok=True)
    (base / "logs" / "server").mkdir(parents=True, exist_ok=True)

def _settings_path(base: Path) -> Path:
    return base / "settings.json"

def set_binaries(base: Path, client: str | None, server: str | None) -> None:
    s: dict[str, Any] = {}
    p = _settings_path(base)
    if p.exists():
        s = json.loads(p.read_text(encoding="utf-8"))
    if client is not None:
        s["client_binary"] = client
    if server is not None:
        s["server_binary"] = server
    p.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")

def get_binary(base: Path, type_: str) -> Path | None:
    p = _settings_path(base)
    if not p.exists():
        return None
    s = json.loads(p.read_text(encoding="utf-8"))
    k = "client_binary" if type_ == "client" else "server_binary"
    v = s.get(k)
    return Path(v) if isinstance(v, str) else None

def save_profile_from_file(base: Path, type_: str, name: str, file_path: Path) -> None:
    data = json.loads(file_path.read_text(encoding="utf-8"))
    out = base / "configs" / type_ / f"{name}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_profile(base: Path, type_: str, name: str) -> dict[str, Any]:
    p = base / "configs" / type_ / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8"))

def list_profiles(base: Path, type_: str) -> list[str]:
    d = base / "configs" / type_
    return [x.stem for x in d.glob("*.json")]

def generate_ini(base: Path, type_: str, name: str) -> Path:
    cfg = load_profile(base, type_, name)
    out_dir = base / "run" / type_ / name
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / ("frpc.ini" if type_ == "client" else "frps.ini")
    lines: list[str] = []
    c = cfg.get("common")
    if isinstance(c, dict):
        lines.append("[common]")
        for k, v in c.items():
            lines.append(f"{k} = {v}")
        lines.append("")
    if type_ == "client":
        ps = cfg.get("proxies")
        if isinstance(ps, list):
            for item in ps:
                if not isinstance(item, dict):
                    continue
                n = item.get("name")
                if isinstance(n, str):
                    lines.append(f"[{n}]")
                    for k, v in item.items():
                        if k == "name":
                            continue
                        lines.append(f"{k} = {v}")
                    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out