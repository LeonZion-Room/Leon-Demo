from pathlib import Path
from flask import Flask, render_template, send_from_directory, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "dev-key"


def to_posix_rel(base: Path, p: Path) -> str:
    return p.relative_to(base).as_posix()


def build_tree(base: Path, current: Path):
    dirs = []
    files = []
    for entry in sorted(current.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if entry.is_dir():
            subtree = build_tree(base, entry)
            dirs.append({
                "type": "dir",
                "name": entry.name,
                "children": subtree["children"],
            })
        else:
            is_html = entry.suffix.lower() in {".html", ".htm"}
            files.append({
                "type": "file",
                "name": entry.name,
                "relpath": to_posix_rel(base, entry),
                "is_html": is_html,
            })
    return {"children": dirs + files}


def get_base_dir() -> Path:
    root_param = request.args.get("root")
    if root_param:
        p = Path(root_param).expanduser()
        session["base_dir"] = str(p)
    base = session.get("base_dir")
    if not base:
        base = str(Path.cwd())
        session["base_dir"] = base
    return Path(base).resolve()


@app.route("/")
def index():
    base_dir = get_base_dir()
    if not base_dir.exists() or not base_dir.is_dir():
        return render_template("index.html", error="路径不可用", base_dir=str(base_dir), tree={"children": []})
    tree = build_tree(base_dir, base_dir)
    return render_template("index.html", base_dir=str(base_dir), tree=tree)


def safe_resolve(base: Path, relpath: str) -> Path:
    target = (base / Path(relpath)).resolve()
    if str(target).startswith(str(base)):
        return target
    raise FileNotFoundError("非法路径")


@app.route("/view/<path:relpath>")
def view_file(relpath: str):
    base_dir = get_base_dir()
    target = safe_resolve(base_dir, relpath)
    if not target.exists() or target.is_dir():
        return redirect(url_for("index"))
    return render_template("view.html", filename=target.name, relpath=relpath)


@app.route("/raw/<path:relpath>")
def raw_file(relpath: str):
    base_dir = get_base_dir()
    target = safe_resolve(base_dir, relpath)
    if not target.exists() or not target.is_file():
        return redirect(url_for("index"))
    return send_from_directory(str(target.parent), target.name)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)