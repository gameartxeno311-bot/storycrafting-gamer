#!/usr/bin/env python3
import json, ssl, sys, urllib.request\nfrom datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from memory import obsidian_memory

MODEL = "storycrafting-gamer"
OLLAMA = "http://127.0.0.1:11434/api/chat"
SYSTEM = "You are The Storycrafting Gamer, a fictional AI influencer focused on game development, storytelling, animation, and world-building. Be friendly, direct, curious, creative, cooperative, hardworking, imaginative, and grounded. Be transparent that you are a fictional AI-created persona. Use the supplied Obsidian memory as persistent context. Do not claim fictional projects are real accomplishments."

def ollama(messages):
    payload = json.dumps({"model": MODEL, "messages": messages, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA, data=payload, method="POST", headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=300) as r: return json.loads(r.read())["message"]["content"]

def main():
    print("The Storycrafting Gamer + Obsidian Memory")
    print("Commands: /remember TEXT, /memory, /clear, /bye")
    history = []
    while True:
        try: user = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt): print(); break
        if not user: continue
        if user.lower() in ("/bye", "/exit", "/quit"): break
        if user.lower() == "/clear": history = []; print("Conversation context cleared."); continue
        if user.lower() == "/memory":
            try: print("\n" + obsidian_memory.read_memory())
            except Exception as e: print("Memory error:", e)
            continue
        if user.lower().startswith("/remember "):
            try: obsidian_memory.append_memory("\n## Memory\n\n" + user[10:].strip()); print("Saved to Obsidian.")
            except Exception as e: print("Memory error:", e)
            continue
        try:
            memory = obsidian_memory.search_memory(user)
        except Exception as e:
            memory = "Obsidian memory unavailable: " + str(e)
        messages = [{"role":"system","content":SYSTEM + "\n\nRelevant Obsidian memory:\n" + memory}] + history + [{"role":"user","content":user}]
        try: answer = ollama(messages)
        except Exception as e: print("Ollama error:", e); continue
        print("\nStorycrafting Gamer: " + answer)
        history.extend([{ "role":"user", "content":user }, { "role":"assistant", "content":answer }])
        history = history[-12:]

if __name__ == "__main__": main()