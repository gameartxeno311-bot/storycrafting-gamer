#!/usr/bin/env python3
import json, sys, urllib.request
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
    req = urllib.request.Request(OLLAMA, data=payload, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as response:
        data = json.loads(response.read())
    return data["message"]["content"]

PENDING_X_FILE = ROOT / "config" / "x_pending.json"

def load_x_pending():
    if not PENDING_X_FILE.exists():
        return None
    return json.loads(PENDING_X_FILE.read_text(encoding="utf-8"))

def clear_x_pending():
    try:
        PENDING_X_FILE.unlink()
    except FileNotFoundError:
        pass

def write_x_pending(data):
    PENDING_X_FILE.parent.mkdir(parents=True, exist_ok=True)
    PENDING_X_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def current_x_account():
    account = x_oauth.account_info()
    if not account:
        raise RuntimeError("No X account is connected.")
    return account

def print_x_posts(result):
    print("\n" + x_oauth.format_posts(result))

def main():
    print("The Storycrafting Gamer + Obsidian Memory")
    print("Commands: /remember TEXT, /memory, /xstatus, /x posts, /x user @HANDLE, /x search QUERY, /x draft TOPIC, /x approve, /x publish, /x cancel, /x clear, /clear, /bye")
    history = []
    while True:
        try:
            user = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        command = user.lower()

        if command in ("/bye", "/exit", "/quit"):
            break
        if command == "/clear":
            history = []
            print("Conversation context cleared.")
            continue
        if command in ("/xstatus", "/x status"):
            try:
                account = x_oauth.account_info()
                pending = load_x_pending()
                print("\nX account: @" + (account.get("username", "unknown") if account else "not connected"))
                if account:
                    metrics = account.get("public_metrics", {})
                    print("Name: " + account.get("name", "unknown"))
                    print("Bio: " + account.get("description", ""))
                    print("Followers: " + str(metrics.get("followers_count", 0)) + " | Following: " + str(metrics.get("following_count", 0)) + " | Posts: " + str(metrics.get("tweet_count", 0)))
                if pending:
                    print("Pending draft: " + pending.get("text", ""))
                    print("Status: " + ("approved" if pending.get("approved") else "awaiting approval"))
            except Exception as exc:
                print("X status error:", exc)
            continue

        if command in ("/x posts", "/x mine"):
            try:
                print_x_posts(x_oauth.account_posts(10))
            except Exception as exc:
                print("X read error:", exc)
            continue

        if command.startswith("/x user "):
            username = user[len("/x user "):].strip()
            try:
                print_x_posts(x_oauth.user_posts(username, 10))
            except Exception as exc:
                print("X user read error:", exc)
            continue

        if command.startswith("/x search "):
            query = user[len("/x search "):].strip()
            try:
                print_x_posts(x_oauth.search_posts(query, 10))
            except Exception as exc:
                print("X search error:", exc)
            continue

        if command.startswith("/x draft "):
            topic = user[len("/x draft "):].strip()
            if not topic:
                print("X draft error: provide a topic.")
                continue
            try:
                account = current_x_account()
                try:
                    memory = obsidian_memory.search_memory(topic)
                except Exception as exc:
                    memory = ""
                    print("[Warning: Obsidian memory unavailable; drafting without it: " + str(exc) + "]")
                draft = ollama([
                    {"role": "system", "content": SYSTEM + "\nDraft exactly one X post, maximum 280 characters. Return only the post text. Do not invent accomplishments."},
                    {"role": "user", "content": "Draft an X post about: " + topic + "\nRelevant memory:\n" + memory},
                ]).strip().strip('"')
                if len(draft) > 280:
                    print("X draft exceeded 280 characters; asking the model to shorten it.")
                    draft = ollama([
                        {"role": "system", "content": SYSTEM + "\nRewrite the supplied X post to 280 characters or fewer. Return only the post text. Preserve the meaning. Do not invent accomplishments."},
                        {"role": "user", "content": draft},
                    ]).strip().strip('"')
                if len(draft) > 280:
                    raise RuntimeError("The generated draft is still over 280 characters.")
                write_x_pending({
                    "text": draft,
                    "approved": False,
                    "account": account.get("username", ""),
                    "created_at": datetime.now().astimezone().isoformat(),
                })
                print("\nX DRAFT for @" + account.get("username", "unknown") + ":")
                print(draft)
                print("\nCharacters: " + str(len(draft)))
                print("Approve with /x approve, then publish with /x publish.")
            except Exception as exc:
                print("X draft error:", exc)
            continue

        if command == "/x approve":
            try:
                pending = load_x_pending()
                if not pending:
                    print("\nNo pending X draft.")
                elif not pending.get("text"):
                    print("\nPending X draft is empty.")
                elif pending.get("approved"):
                    print("\nX draft is already approved. Publish with /x publish.")
                else:
                    pending["approved"] = True
                    pending["approved_at"] = datetime.now().astimezone().isoformat()
                    write_x_pending(pending)
                    print("\nX draft approved. Publish with /x publish.")
            except Exception as exc:
                print("X approval error:", exc)
            continue

        if command == "/x publish":
            try:
                pending = load_x_pending()
                if not pending:
                    print("\nNo pending X draft.")
                elif not pending.get("approved"):
                    print("\nThis draft has not been approved. Use /x approve first.")
                else:
                    account = current_x_account()
                    expected = pending.get("account", "")
                    actual = account.get("username", "")
                    if expected and expected.lower() != actual.lower():
                        raise RuntimeError("The connected X account changed since this draft was created. Create a new draft before publishing.")
                    text = pending.get("text", "").strip()
                    if not text:
                        raise RuntimeError("Pending X draft is empty.")
                    if len(text) > 280:
                        raise RuntimeError("Pending X draft exceeds 280 characters.")
                    result = x_oauth.post(text)
                    post_id = result.get("data", {}).get("id")
                    if not post_id:
                        raise RuntimeError("X API returned no post ID; pending draft was kept.")
                    clear_x_pending()
                    print("\nX post published successfully.")
                    print("Post ID: " + str(post_id))
            except Exception as exc:
                print("X publish error: " + str(exc))
            continue

        if command == "/x cancel" or command == "/x clear":
            clear_x_pending()
            print("\nPending X draft cancelled.")
            continue

        if command == "/memory":
            try:
                print("\n" + obsidian_memory.read_memory())
            except Exception as exc:
                print("Memory error: " + str(exc))
            continue

        if command.startswith("/remember "):
            memory_text = user[len("/remember "):].strip()
            if not memory_text:
                print("Memory error: provide memory text.")
                continue
            try:
                obsidian_memory.append_memory("### " + memory_text)
                print("Saved to Obsidian.")
            except Exception as exc:
                print("Memory error: " + str(exc))
            continue

        try:
            memory = obsidian_memory.search_memory(user)
        except Exception as exc:
            memory = "Obsidian memory unavailable: " + str(exc)
            print("[Warning: " + memory + "]")
        try:
            account = x_oauth.account_info()
            if account:
                x_context = (
                    "\n\nX ACCOUNT STATUS: Connected. You can inspect this account's profile and recent posts, "
                    "and search public posts from other accounts. The user can request /x posts, /x user @handle, "
                    "or /x search query. Connected account: @" + account.get("username", "unknown") +
                    " (" + account.get("name", "unknown") + "). Do not claim you inspected X unless an X read command returned data. "
                    "Do not claim a post was published unless the X posting command/API reports success."
                )
            else:
                x_context = "\n\nX ACCOUNT STATUS: No X account is currently connected. The user can connect one from the launcher."
        except Exception as exc:
            x_context = "\n\nX ACCOUNT STATUS: Unable to verify the X connection right now: " + str(exc)
        messages = [{"role": "system", "content": SYSTEM + x_context + "\n\nRelevant Obsidian memory:\n" + memory}] + history + [{"role": "user", "content": user}]
        try:
            answer = ollama(messages)
        except Exception as exc:
            print("Ollama error: " + str(exc))
            continue
        print("\nStorycrafting Gamer: " + answer)
        try:
            timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
            obsidian_memory.append_chat_log(
                "### " + timestamp + "\n\n**You:** " + user +
                "\n\n**Storycrafting Gamer:** " + answer
            )
            print("[Chat logged to Obsidian]")
        except Exception as exc:
            print("[Warning: chat was not logged to Obsidian: " + str(exc) + "]")
        history.extend([{"role": "user", "content": user}, {"role": "assistant", "content": answer}])
        history = history[-12:]

if __name__ == "__main__":
    main()
