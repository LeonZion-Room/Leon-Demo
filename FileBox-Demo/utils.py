import os
import re
import json
import time
import uuid

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "storage")
BATCHES_FILE = os.path.join(STORAGE_DIR, "batches.json")
AUTH_FILE = os.path.join(STORAGE_DIR, "auth_tokens.json")

def ensure_storage():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

def load_batches():
    ensure_storage()
    if not os.path.exists(BATCHES_FILE):
        return {}
    try:
        with open(BATCHES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_batches(data):
    ensure_storage()
    with open(BATCHES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def to_safe_filename(name):
    name = name.strip()
    name = name.replace(" ", "_")
    name = re.sub(r"[<>:\\/\|\?\*]", "", name)
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    name = name.strip(".")
    if not name:
        name = "file"
    if len(name) > 120:
        root, ext = os.path.splitext(name)
        name = root[:100] + ext
    return name

def unique_filename(dirpath, safe_name):
    base, ext = os.path.splitext(safe_name)
    candidate = safe_name
    i = 2
    while os.path.exists(os.path.join(dirpath, candidate)):
        candidate = f"{base}-{i}{ext}"
        i += 1
    return candidate

def load_auth_tokens():
    ensure_storage()
    if not os.path.exists(AUTH_FILE):
        return {}
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_auth_tokens(data):
    ensure_storage()
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_token(ttl_seconds=604800):
    tokens = load_auth_tokens()
    t = uuid.uuid4().hex
    exp = int(time.time()) + int(ttl_seconds)
    tokens[t] = exp
    save_auth_tokens(tokens)
    return t

def verify_token(token):
    if not token:
        return False
    now = int(time.time())
    tokens = load_auth_tokens()
    changed = False
    expired = [k for k, v in tokens.items() if v < now]
    if expired:
        for k in expired:
            tokens.pop(k, None)
        changed = True
    if changed:
        save_auth_tokens(tokens)
    return token in tokens and tokens[token] >= now

def revoke_token(token):
    if not token:
        return
    tokens = load_auth_tokens()
    if token in tokens:
        tokens.pop(token)
        save_auth_tokens(tokens)