"""Google OAuth2 service for Antigravity: token refresh, userinfo, and loopback login."""

import http.server
import json
import secrets
import threading
import urllib.parse
import urllib.request
import webbrowser
from typing import Optional

from ..core.constants import (
    AUTH_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    HTTP_TIMEOUT_SECONDS,
    OAUTH_SCOPES,
    TOKEN_URL,
    USERINFO_URL,
)

SUCCESS_HTML = """<!DOCTYPE html>
<html>
<head><title>Betteragy - Authentication Successful</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
             display: flex; justify-content: center; align-items: center; height: 100vh;
             margin: 0; background: #0d1117; color: #c9d1d9;">
  <div style="text-align: center; padding: 40px; background: #161b22;
              border-radius: 12px; border: 1px solid #30363d; max-width: 480px;">
    <h1 style="color: #58a6ff; margin-bottom: 12px;">[OK] Authenticated!</h1>
    <p style="font-size: 16px; line-height: 1.5; color: #8b949e;">
      Account <b style="color: #f0f6fc;">{email}</b> has been connected to Betteragy.<br>
      You can now close this browser tab and return to your terminal.
    </p>
  </div>
</body>
</html>"""


def _direct_urlopen(req: urllib.request.Request, timeout: float = HTTP_TIMEOUT_SECONDS):
    """Open HTTP request bypassing any environment or system proxy."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(req, timeout=timeout)


def refresh_access_token(refresh_token: str) -> dict:
    """Exchange a refresh token for a fresh access token."""
    payload = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode("utf-8")

    req = urllib.request.Request(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with _direct_urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_user_info(access_token: str) -> dict:
    """Fetch user profile information (email, name, picture) using access token."""
    req = urllib.request.Request(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    with _direct_urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def exchange_code(code: str, redirect_uri: str) -> dict:
    """Exchange an authorization code for token pair."""
    payload = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode("utf-8")

    req = urllib.request.Request(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with _direct_urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


def start_oauth_flow(port: int = 19876, timeout_secs: int = 120) -> Optional[dict]:
    """Execute OAuth 2.0 loopback server flow in the default browser."""
    redirect_uri = f"http://127.0.0.1:{port}/callback"
    state = secrets.token_hex(16)
    auth_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(OAUTH_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"

    result: dict = {}
    done_event = threading.Event()

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Silent logging

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return

            query = urllib.parse.parse_qs(parsed.query)
            code = query.get("code", [""])[0]
            ret_state = query.get("state", [""])[0]

            if not code or ret_state != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid authorization code or state.")
                done_event.set()
                return

            try:
                tokens = exchange_code(code, redirect_uri)
                user_info = fetch_user_info(tokens["access_token"])
                result["tokens"] = tokens
                result["user_info"] = user_info

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = SUCCESS_HTML.format(email=user_info.get("email", "Account"))
                self.wfile.write(html.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Authentication failed: {e}".encode("utf-8"))
            finally:
                done_event.set()

    server = http.server.HTTPServer(("127.0.0.1", port), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        webbrowser.open(auth_url)
        done = done_event.wait(timeout=timeout_secs)
        if not done or "tokens" not in result:
            return None
        return result
    finally:
        server.shutdown()
        server.server_close()
