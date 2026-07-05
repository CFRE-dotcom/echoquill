"""OAuth 2.0 sign-in (PKCE) - "log in with your account" instead of an API key.

Fully working plumbing: opens the provider's login page in your browser,
catches the redirect on localhost, exchanges the code for tokens, refreshes
them automatically, and stores them encrypted (DPAPI) in your config.

Activation requires a Client ID issued by the provider's developer program
(e.g. OpenAI's "Sign in with ChatGPT" program). Enter it in Settings once
approved and press Sign in.
"""

import base64
import hashlib
import http.server
import secrets
import threading
import time
import urllib.parse
import webbrowser

REDIRECT_PORT = 8765
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"


def _pkce_pair():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        q = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(q)
        _CallbackHandler.code = (params.get("code") or [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        ok = _CallbackHandler.code is not None
        self.wfile.write((
            "<html><body style='font-family:sans-serif;background:#1c1c1e;"
            "color:#f2f2f7;text-align:center;padding-top:80px'>"
            + ("<h2>✓ Signed in</h2><p>You can close this tab and go back to EchoQuill.</p>"
               if ok else "<h2>Sign-in failed</h2><p>No code received.</p>")
            + "</body></html>").encode())

    def log_message(self, *a):
        pass


def sign_in(cfg: dict, status_cb=lambda s: None) -> dict:
    """Run the full PKCE flow. Returns token dict or raises."""
    client_id = cfg.get("ai_oauth_client_id", "").strip()
    auth_url = cfg.get("ai_oauth_auth_url", "").strip()
    token_url = cfg.get("ai_oauth_token_url", "").strip()
    if not client_id:
        raise RuntimeError("No Client ID set. Apply to the provider's developer "
                           "program, then paste the Client ID here.")
    if not auth_url or not token_url:
        raise RuntimeError("This provider has no OAuth endpoints configured.")

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": cfg.get("ai_oauth_scope", "openid profile email offline_access"),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    url = auth_url + "?" + urllib.parse.urlencode(params)

    _CallbackHandler.code = None
    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), _CallbackHandler)
    threading.Thread(target=server.handle_request, daemon=True).start()

    status_cb("Opening your browser to sign in…")
    webbrowser.open(url)

    deadline = time.time() + 300
    while _CallbackHandler.code is None and time.time() < deadline:
        time.sleep(0.5)
    try:
        server.server_close()
    except Exception:
        pass
    if _CallbackHandler.code is None:
        raise RuntimeError("Timed out waiting for the sign-in to finish.")

    status_cb("Finishing sign-in…")
    import requests
    resp = requests.post(token_url, data={
        "grant_type": "authorization_code",
        "code": _CallbackHandler.code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "code_verifier": verifier,
    }, timeout=30)
    resp.raise_for_status()
    tok = resp.json()
    tok["obtained_at"] = time.time()
    return tok


def get_access_token(cfg: dict, save_cb=None) -> str:
    """Current access token, refreshing it automatically when expired."""
    tok = cfg.get("ai_oauth_tokens") or {}
    access = tok.get("access_token", "")
    if not access:
        return ""
    expires_in = tok.get("expires_in")
    if expires_in and time.time() > tok.get("obtained_at", 0) + float(expires_in) - 120:
        refresh = tok.get("refresh_token")
        if refresh:
            try:
                import requests
                resp = requests.post(cfg.get("ai_oauth_token_url", ""), data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh,
                    "client_id": cfg.get("ai_oauth_client_id", ""),
                }, timeout=30)
                resp.raise_for_status()
                new = resp.json()
                new.setdefault("refresh_token", refresh)
                new["obtained_at"] = time.time()
                cfg["ai_oauth_tokens"] = new
                if save_cb:
                    save_cb(cfg)
                return new.get("access_token", "")
            except Exception:
                return access   # try the old one; worst case a 401
    return access
