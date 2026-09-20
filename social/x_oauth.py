import base64
import hashlib
import json
import os
import secrets
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "config" / ".env"
TOKEN_FILE = ROOT / "config" / "x_tokens.json"
DEFAULT_REDIRECT = "http://127.0.0.1:8765/callback"
AUTH_URL = "https://x.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
API_BASE = "https://api.x.com/2"

SCOPES = ["tweet.read", "tweet.write", "users.read", "offline.access"]


def load_env():
    values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    values.update({k: v for k, v in os.environ.items() if k.startswith("X_")})
    return values


def save_tokens(tokens):
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:
        pass


def load_tokens():
    if not TOKEN_FILE.exists():
        return None
    return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))


def request_json(url, method="GET", data=None, headers=None):
    body = None
    final_headers = {"Accept": "application/json"}
    if headers:
        final_headers.update(headers)
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        final_headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=body, headers=final_headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def refresh_token(client_id, refresh):
    data = {
        "refresh_token": refresh,
        "grant_type": "refresh_token",
        "client_id": client_id,
    }
    result = request_json(TOKEN_URL, method="POST", data=data)
    if "refresh_token" not in result:
        result["refresh_token"] = refresh
    result["expires_at"] = int(time.time()) + int(result.get("expires_in", 7200))
    save_tokens(result)
    return result


def access_token(client_id):
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No X authorization found. Run: python social\\x_oauth.py connect")
    expires_at = tokens.get("expires_at", 0)
    if time.time() >= expires_at - 60:
        refresh = tokens.get("refresh_token")
        if not refresh:
            raise RuntimeError("The X access token expired and no refresh token is available.")
        tokens = refresh_token(client_id, refresh)
    return tokens["access_token"]


def connect():
    env = load_env()
    client_id = env.get("X_CLIENT_ID")
    redirect_uri = env.get("X_REDIRECT_URI", DEFAULT_REDIRECT)
    if not client_id:
        raise RuntimeError("Set X_CLIENT_ID in config/.env before connecting.")

    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    state = secrets.token_urlsafe(24)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)

    parsed = urllib.parse.urlparse(redirect_uri)
    if parsed.hostname not in ("127.0.0.1", "localhost"):
        raise RuntimeError("This launcher expects a local redirect URI such as http://127.0.0.1:8765/callback.")

    result = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            result["code"] = query.get("code", [None])[0]
            result["state"] = query.get("state", [None])[0]
            result["error"] = query.get("error", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Authorization received.</h2><p>You can close this window and return to The Storycrafting Gamer.</p></body></html>")

        def log_message(self, *args):
            pass

    server = HTTPServer((parsed.hostname, parsed.port or 80), CallbackHandler)
    print("Opening X authorization in your browser...")
    print("If the browser does not open, copy this URL:")
    print(url)
    webbrowser.open(url)
    server.timeout = 180
    deadline = time.time() + 180
    while time.time() < deadline and "code" not in result and "error" not in result:
        server.handle_request()
    server.server_close()

    if result.get("error"):
        raise RuntimeError(f"X authorization failed: {result['error']}")
    if result.get("state") != state:
        raise RuntimeError("OAuth state validation failed.")
    if not result.get("code"):
        raise RuntimeError("Timed out waiting for the X authorization callback.")

    token_data = {
        "code": result["code"],
        "grant_type": "authorization_code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    }
    tokens = request_json(TOKEN_URL, method="POST", data=token_data)
    tokens["expires_at"] = int(time.time()) + int(tokens.get("expires_in", 7200))
    save_tokens(tokens)
    print("X account authorized successfully.")
    print("Token data was saved locally and is excluded from Git.")


def api_get(path, client_id):
    token = access_token(client_id)
    request = urllib.request.Request(
        API_BASE + path,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def post(text):
    env = load_env()
    client_id = env.get("X_CLIENT_ID")
    if not client_id:
        raise RuntimeError("Set X_CLIENT_ID in config/.env.")
    token = access_token(client_id)
    payload = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        API_BASE + "/tweets",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    print("Post created successfully.")
    print(json.dumps(result, indent=2))


def account_info():
    """Return the currently authorized X account, or None if not connected."""
    env = load_env()
    client_id = env.get("X_CLIENT_ID")
    if not client_id or not load_tokens():
        return None
    data = api_get("/users/me", client_id)
    return data.get("data", {})


def status():
    env = load_env()
    client_id = env.get("X_CLIENT_ID")
    if not client_id:
        print("X_CLIENT_ID is not configured.")
        return
    tokens = load_tokens()
    if not tokens:
        print("X is not connected.")
        return
    try:
        user = account_info() or {}
        print(f"Connected X account: @{user.get('username', 'unknown')} ({user.get('name', 'unknown')})")
    except Exception as exc:
        print(f"X connection check failed: {exc}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python social\\x_oauth.py connect|status|post \"text\"")
        raise SystemExit(2)
    command = sys.argv[1].lower()
    if command == "connect":
        connect()
    elif command == "status":
        status()
    elif command == "post":
        if len(sys.argv) < 3:
            raise RuntimeError("Provide post text.")
        post(" ".join(sys.argv[2:]))
    else:
        raise RuntimeError(f"Unknown command: {command}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
