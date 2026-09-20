#!/usr/bin/env python3
import json, ssl, sys, urllib.request
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from memory import obsidian_memory
from social import x_oauth

MODEL = "storycrafting-gamer"
OLLAMA = "http://127.0.0.1:11434/api/chat"
SYSTEM = "You are The Storycrafting Gamer, a fictional AI influencer focused on game development, storytelling, animation, and world-building. Be friendly, direct, curious, creative, cooperative, hardworking, imaginative, and grounded. Be transparent that you are a fictional AI-created persona. Use the supplied Obsidian memory as persistent context. Do not claim fictional projects are real accomplishments."

def ollama(messages):
    payload = json.dumps({"model": MODEL, "messages": messages, "stream": False}).encode()
    req = urllib.request.Request(OLLAMA, data=payload, method="POST", headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=300) as r: return json.loads(r.read())["message"]["content"]

def main():
    print("The Storycrafting Gamer + Obsidian Memory")
    print("Commands: /remember TEXT, /memory, /xstatus, /clear, /bye")
    history = []
    while True:
        try: user = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt): print(); break
        if not user: continue
        if user.lower() in ("/bye", "/exit", "/quit"): break
        if user.lower() == "/clear": history = []; print("Conversation context cleared."); continue
        if user.lower() == "/xstatus":
            try:
                account = x_oauth.account_info()
                if account:
                    print(f"\nX account connected: @{account.get('username', 'unknown')} ({account.get('name', 'unknown')})")
                else:
                    print("\nNo X account is currently connected.")
            except Exception as e:
                print("X status error:", e)
            continue
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
        try:
            account = x_oauth.account_info()
            if account:
                x_context = ("\n\nX ACCOUNT STATUS: Connected. You are authorized to the X account @" +
                    account.get("username", "unknown") + " (" + account.get("name", "unknown") + "). " +
                    "The local X integration can check this account and publish posts through the X API. " +
                    "Do not claim a post was published unless the X posting command/API reports success.")
            else:
                x_context = "\n\nX ACCOUNT STATUS: No X account is currently connected. The user can connect one from the launcher."
        except Exception as e:
            x_context = "\n\nX ACCOUNT STATUS: Unable to verify the X connection right now: " + str(e)
        messages = [{"role":"system","content":SYSTEM + x_context + "\n\nRelevant Obsidian memory:\n" + memory}] + history + [{"role":"user","content":user}]
        try: answer = ollama(messages)
        except Exception as e: print("Ollama error:", e); continue
        print("\nStorycrafting Gamer: " + answer)
        try:
            timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
            obsidian_memory.append_chat_log(
                "### " + timestamp + "\n\n**You:** " + user +
                "\n\n**Storycrafting Gamer:** " + answer
            )
            print("[Chat logged to Obsidian]")
        except Exception as e:
            print("[Warning: chat was not logged to Obsidian: " + str(e) + "]")
        history.extend([{ "role":"user", "content":user }, { "role":"assistant", "content":answer }])
        history = history[-12:]

if __name__ == "__main__": main()