#!/usr/bin/env python3
"""Obsidian Local REST API memory bridge for The Storycrafting Gamer."""
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

def request(method, path, data=None, headers=None):
    env = load_env()
    base_url = env.get("OBSIDIAN_URL", DEFAULT_URL).rstrip("/")
    api_key = env.get("OBSIDIAN_API_KEY", "")
    if not api_key:
        raise RuntimeError("OBSIDIAN_API_KEY is not configured in config/.env")
    body = None
    if data is not None:
        body = data.encode("utf-8") if isinstance(data, str) else json.dumps(data).encode("utf-8")
    request_headers = {"Authorization": "Bearer " + api_key}
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(base_url + path, data=body, method=method, headers=request_headers)
    context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, context=context, timeout=10) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Obsidian HTTP {exc.code}: {detail or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Obsidian Local REST API: {exc.reason}") from exc

def note_path():
    env = load_env()
    note = env.get("OBSIDIAN_MEMORY_NOTE", DEFAULT_NOTE)
    return "/vault/" + quote(note, safe="/")

def ensure_note():
    path = note_path()
    try:
        request("GET", path)
        return
    except RuntimeError as exc:
        if "Obsidian HTTP 404" not in str(exc):
            raise
    content = (
        "# Storycrafting Gamer Memory\n\n"
        "## Memories\n\n"
        "## Chat Log\n\n"
    )
    request("PUT", path, content, {"Content-Type": "text/markdown"})

def read_memory():
    ensure_note()
    return request("GET", note_path())

def append_to_heading(heading, text):
    ensure_note()
    instruction = {
        "targetType": "heading",
        "target": [heading],
        "operation": "append",
        "content": text.rstrip() + "\n",
        "createTargetIfMissing": True,
    }
    return request(
        "PATCH",
        note_path(),
        instruction,
        {"Content-Type": "application/json"},
    )

def append_memory(text):
    return append_to_heading("Memories", text)

def append_chat_log(text):
    return append_to_heading("Chat Log", text)

def search_memory(query):
    query = query.strip()
    if not query:
        return ""
    path = "/search/simple/?query=" + quote(query, safe="")
    raw = request("POST", path)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if not isinstance(result, list):
        return json.dumps(result, ensure_ascii=False)
    snippets = []
    for item in result[:8]:
        if isinstance(item, str):
            snippets.append(item)
            continue
        if not isinstance(item, dict):
            continue
        path_value = item.get("filename") or item.get("path") or item.get("file") or ""
        matches = item.get("matches") or item.get("match") or item.get("text") or item.get("content") or ""
        if isinstance(matches, list):
            matches = " ".join(str(x) for x in matches)
        snippets.append((str(path_value) + ": " if path_value else "") + str(matches))
    return "\n\n".join(snippets)

def status():
    try:
        ensure_note()
        print("Obsidian Local REST API: connected")
        print("Memory note: " + note_path().removeprefix("/vault/"))
        return True
    except Exception as exc:
        print("Obsidian connection failed: " + str(exc))
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python memory\\obsidian_memory.py status|read|remember \"text\"|search \"query\"")
        raise SystemExit(2)
    command = sys.argv[1].lower()
    try:
        if command == "status":
            raise SystemExit(0 if status() else 1)
        if command == "read":
            print(read_memory())
            return
        if command == "remember":
            if len(sys.argv) < 3:
                raise RuntimeError("Provide memory text.")
            append_memory("### " + " ".join(sys.argv[2:]).strip())
            print("Memory saved to Obsidian.")
            return
        if command == "search":
            if len(sys.argv) < 3:
                raise RuntimeError("Provide a search query.")
            result = search_memory(" ".join(sys.argv[2:]))
            print(result or "No matching memory found.")
            return
        raise RuntimeError("Unknown command: " + command)
    except Exception as exc:
        print("Error: " + str(exc))
        raise SystemExit(1)

if __name__ == "__main__":
    main()
