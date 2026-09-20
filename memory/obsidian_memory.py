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
            if not line or line.startswith("#") or "=" not in line: continue
            k, v = line.split("=", 1); values[k.strip()] = v.strip().strip('"').strip("'")
    return values

ENV = load_env()
BASE_URL = ENV.get("OBSIDIAN_URL", DEFAULT_URL).rstrip("/")
API_KEY = ENV.get("OBSIDIAN_API_KEY", "")
MEMORY_NOTE = ENV.get("OBSIDIAN_MEMORY_NOTE", DEFAULT_NOTE)

def request(method, path, data=None, headers=None):
    if not API_KEY: raise RuntimeError("OBSIDIAN_API_KEY is not configured in config/.env")
    body = None if data is None else data.encode("utf-8") if isinstance(data, str) else json.dumps(data).encode("utf-8")
    h = {"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"}
    if headers: h.update(headers)
    req = urllib.request.Request(BASE_URL + path, data=body, method=method, headers=h)
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=context, timeout=10) as r: return r.read().decode("utf-8")

def ensure_note():
    path = "/vault/" + quote(MEMORY_NOTE, safe="/")
    try: request("GET", path)
    except urllib.error.HTTPError as e:
        if e.code != 404: raise
        request("PUT", path, "# Storycrafting Gamer Memory\n\n")

def read_memory():
    ensure_note(); return request("GET", "/vault/" + quote(MEMORY_NOTE, safe="/"))

def append_memory(text):
    ensure_note()
    path = "/vault/" + quote(MEMORY_NOTE, safe="/")
    return request("PATCH", path, text.rstrip() + "\n", {"Operation":"append", "Target-Type":"heading", "Target":"Storycrafting Gamer Memory"})

def search_memory(query):
    return request("POST", "/search/simple/", {"query": query, "contextLength": 4000})

def status():
    req = urllib.request.Request(BASE_URL + "/", method="GET")
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=context, timeout=10) as r: return r.read().decode("utf-8")

def main():
    if len(sys.argv) < 2: print("Usage: python memory\\obsidian_memory.py status|read|remember TEXT|search QUERY"); return 2
    try:
        cmd = sys.argv[1].lower()
        if cmd == "status": print(status())
        elif cmd == "read": print(read_memory())
        elif cmd == "remember":
            if len(sys.argv) < 3: raise RuntimeError("Provide memory text.")
            append_memory("\n## Memory\n\n" + " ".join(sys.argv[2:])); print("Memory saved to Obsidian:", MEMORY_NOTE)
        elif cmd == "search":
            if len(sys.argv) < 3: raise RuntimeError("Provide a search query.")
            print(search_memory(" ".join(sys.argv[2:])))
        else: raise RuntimeError("Unknown command: " + cmd)
        return 0
    except Exception as e: print("Obsidian memory error:", e); return 1

if __name__ == "__main__": raise SystemExit(main())