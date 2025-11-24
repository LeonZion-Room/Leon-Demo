from flask import Flask, render_template, jsonify, request, Response
import os
import sys
import json
import re
from urllib.parse import urlparse, urljoin

try:
    import requests
except Exception:
    requests = None

BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(BASE_PATH, 'templates'), static_folder=os.path.join(BASE_PATH, 'static'))

# 当打包为 exe 时，将数据目录定位到可写的工作目录
BASE_DIR = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LAYOUT_PATH = os.path.join(DATA_DIR, 'layout.json')

def ensure_data_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LAYOUT_PATH):
        default = {
            "cellHeight": 120,
            "margin": 0,
            "headerCollapsed": True,
            "locked": False,
            "theme": {
                "mode": "light",
                "primary": "#1677ff",
                "bg": "#f7f8fa",
                "card": "#ffffff",
                "grid": "#eaeaea",
                "text": "#1f1f1f"
            },
            "items": []
        }
        with open(LAYOUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(default, f, ensure_ascii=False, indent=2)

def load_layout():
    ensure_data_file()
    with open(LAYOUT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_layout(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LAYOUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/layout", methods=["GET", "POST"])
def api_layout():
    if request.method == "GET":
        return jsonify(load_layout())
    data = request.get_json(force=True, silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "invalid payload"}), 400
    save_layout(data)
    return jsonify({"status": "ok"})

@app.route('/proxy')
def proxy():
    target = request.args.get('url', '').strip()
    hide_scroll = request.args.get('hide_scroll', '0') == '1'
    if not target:
        return Response('Missing url', status=400)
    if requests is None:
        return Response('requests library not installed', status=500)
    try:
        resp = requests.get(target, timeout=10, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True)
    except Exception as e:
        return Response(f'Fetch failed: {e}', status=502)
    ct = resp.headers.get('Content-Type', '')
    content = resp.content
    # Only rewrite HTML
    if 'text/html' in ct:
        text = resp.text
        # Inject <base> to fix relative paths
        # If <head> exists, insert <base>; otherwise create minimal head
        parsed = urlparse(resp.url)
        base_href = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if '<head' in text:
            inject = f"\n<base href=\"{base_href}\">"
            if hide_scroll:
                inject += ("\n<style>"
                           "html,body{overflow:hidden!important;}"
                           "html{scrollbar-width:none!important;}"
                           "*{scrollbar-width:none!important;}"
                           "::-webkit-scrollbar{width:0!important;height:0!important;display:none!important;}"
                           "</style>")
            script_js = (
                "(function(){try{"
                "var mo=new MutationObserver(function(){document.querySelectorAll(\"a[target='_blank']\").forEach(function(a){a.setAttribute('target','_self');});});"
                "mo.observe(document.documentElement,{subtree:true,childList:true});"
                "document.addEventListener('click',function(e){var a=e.target.closest('a[href]'); if(a){a.setAttribute('target','_self');}});"
                "var _open=window.open; window.open=function(u){try{return _open.call(window,u,'_self');}catch(e){return _open(u);}};"
                "}catch(e){}})();"
            )
            inject += ("\n<script>" + script_js + "</script>")
            text = re.sub(r'<head[^>]*>', lambda m: m.group(0) + inject, text, count=1, flags=re.IGNORECASE)
        else:
            css = "<style>" + ("html,body{overflow:hidden!important;} html{scrollbar-width:none!important;} *{scrollbar-width:none!important;} ::-webkit-scrollbar{width:0!important;height:0!important;display:none!important;}" if hide_scroll else "") + "</style>"
            script_js = (
                "(function(){try{"
                "var mo=new MutationObserver(function(){document.querySelectorAll(\"a[target='_blank']\").forEach(function(a){a.setAttribute('target','_self');});});"
                "mo.observe(document.documentElement,{subtree:true,childList:true});"
                "document.addEventListener('click',function(e){var a=e.target.closest('a[href]'); if(a){a.setAttribute('target','_self');}});"
                "var _open=window.open; window.open=function(u){try{return _open.call(window,u,'_self');}catch(e){return _open(u);}};"
                "}catch(e){}})();"
            )
            script = ("<script>" + script_js + "</script>")
            text = f"<head><base href=\"{base_href}\">{css}{script}</head>" + text
        content = text.encode('utf-8')
        ct = 'text/html; charset=utf-8'
    # Return without frame-blocking headers
    headers = {
        'Content-Type': ct or 'application/octet-stream',
        'Cache-Control': 'no-cache',
    }
    return Response(content, headers=headers)

if __name__ == "__main__":
    ensure_data_file()
    app.run(host="127.0.0.1", port=5000, debug=True)
