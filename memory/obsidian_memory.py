#!/usr/bin/env python3
"""Obsidian memory bridge for The Storycrafting Gamer."""
import json, os, ssl, sys, urllib.error, urllib.request
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "config" / ".env"
DEFAULT_URL = "https://127.0.0.1:27124"
DEFAULT_NOTE = "Storycrafting Gamer/AI Memory.md"

def load_env():
    values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip('"').strip("'")
    return values

ENV = load_env()
BASE_URL = ENV.get("OBSIDIAN_URL", DEFAULT_URL).rstrip("/")
API_KEY = ENV.get("OBSIDIAN_API_KEY", "")
MEMORY_NOTE = ENV.get("OBSIDIAN_MEMORY_NOTE", DEFAULT_NOTE)

def request(method, path, data=None, headers=None, require_auth=True):
    if not API_KEY:
        raise RuntimeError("OBSIDIAN_API_KEY is not configured in config/.env")
    body = None if data is None else data.encode("utf-8") if isinstance(data, str) else json.dumps(data).encode("utf-8")
    h = {"Authorization": "Bearer " + API_KEY}
    if headers:
        h.update(headers)
    req = urllib.request.Request(BASE_URL + path, data=body, method=method, headers=h)
    context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, context=context, timeout=10) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Obsidian HTTP {e.code}: {detail or e.reason}") from e

def ensure_note():
    path = "/vault/" + quote(MEMORY_NOTE, safe="/")
    try:
        request("GET", path)
    except Exception as e:
        if "Obsidian HTTP 404" not in str(e):
            raise
        request("PUT", path, "# Storycrafting Gamer Memory\n\n", {"Content-Type": "text/markdown"})

def read_memory():
    ensure_note()
    return request("GET", "/vault/" + quote(MEMORY_NOTE, safe="/"))

def append_memory(text):
    ensure_note()
    path = "/vault/" + quote(MEMORY_NOTE, safe="/")
    instruction = {
        "targetType": "heading",
        "target": ["Storycrafting Gamer Memory"],
        "operation": "append",
        "content": text.rstrip() + "\\n",
        "createTargetIfMissing": True
    }
    try:
        return request("PATCH", path, instruction, {
            "Content-Type": "application/json"
        })
    except RuntimeError as e:
        if "Obsidian HTTP 400" not in str(e) and "Obsidian HTTP 415" not in str(e) and "Obsidian HTTP 422" not in str(e):
            raise
        return request("PATCH", path, text.rstrip() + "\\n", {
            "Operation": "append",
            "Target-Type": "heading",
            "Target": "%5B%22Storycrafting%20Gamer%20Memory%22%5D",
            "Markdown-Patch-Version": "2",
            "Content-Type": "text/markdown"
        })

def append_chat_log(text):
    ensure_note()
    path = "/vault/" + quote(MEMORY_NOTE, safe="/")
    instruction = {
        "targetType": "heading",
        "target": ["Chat Log"],
        "operation": "append",
        "content": text.rstrip() + "\\n",
        "createTargetIfMissing": True
    }
    return request("PATCH", path, instruction, {
        "Content-Type": "application/json"
    })

