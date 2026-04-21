# brokers/schwab_oauth.py
from __future__ import annotations
import base64
import json
import os
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, Dict, Any

import requests  # pip install requests


AUTHORIZE_URL = "https://api.schwabapi.com/v1/oauth/authorize"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"  # 常見做法；若你後續以官方文件為準調整


@dataclass
class SchwabTokens:
    access_token: str
    refresh_token: str
    expires_at: float  # epoch seconds


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("utf-8")


def build_login_url(client_id: str, redirect_uri: str) -> str:
    q = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
    }
    return AUTHORIZE_URL + "?" + urllib.parse.urlencode(q)


class _CodeHandler(BaseHTTPRequestHandler):
    # shared state
    auth_code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if "error" in qs:
            _CodeHandler.error = qs.get("error", ["unknown"])[0]
        if "code" in qs:
            _CodeHandler.auth_code = qs.get("code", [""])[0]

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("✅ Schwab OAuth 完成，你可以關掉這個分頁回到程式。".encode("utf-8"))

    def log_message(self, format, *args):
        return  # silence


def wait_for_auth_code(redirect_host: str = "127.0.0.1", redirect_port: int = 8787, timeout_sec: int = 180) -> str:
    _CodeHandler.auth_code = None
    _CodeHandler.error = None

    server = HTTPServer((redirect_host, redirect_port), _CodeHandler)

    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()

    t0 = time.time()
    try:
        while time.time() - t0 < timeout_sec:
            if _CodeHandler.error:
                raise RuntimeError(f"OAuth error: {_CodeHandler.error}")
            if _CodeHandler.auth_code:
                return _CodeHandler.auth_code
            time.sleep(0.2)
        raise TimeoutError("等待 OAuth callback 超時")
    finally:
        server.shutdown()
        server.server_close()


def exchange_code_for_refresh_token(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    auth_code: str,
) -> SchwabTokens:
    headers = {
        "Authorization": _basic_auth_header(client_id, client_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
    }
    r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
    r.raise_for_status()
    js = r.json()

    # expires_in 通常是秒
    expires_in = float(js.get("expires_in", 1800))
    return SchwabTokens(
        access_token=str(js.get("access_token", "")),
        refresh_token=str(js.get("refresh_token", "")),
        expires_at=time.time() + expires_in - 30,
    )


def refresh_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> SchwabTokens:
    headers = {
        "Authorization": _basic_auth_header(client_id, client_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
    r.raise_for_status()
    js = r.json()
    expires_in = float(js.get("expires_in", 1800))
    # 有些實作 refresh 會回新的 refresh_token；有些不會
    new_refresh = str(js.get("refresh_token", refresh_token))
    return SchwabTokens(
        access_token=str(js.get("access_token", "")),
        refresh_token=new_refresh,
        expires_at=time.time() + expires_in - 30,
    )


def save_tokens(path: str, t: SchwabTokens) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(t.__dict__, f, ensure_ascii=False, indent=2)


def load_tokens(path: str) -> Optional[SchwabTokens]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return SchwabTokens(
        access_token=d.get("access_token", ""),
        refresh_token=d.get("refresh_token", ""),
        expires_at=float(d.get("expires_at", 0)),
    )


def get_valid_access_token(
    client_id: str,
    client_secret: str,
    token_path: str,
) -> SchwabTokens:
    t = load_tokens(token_path)
    if t and t.access_token and time.time() < t.expires_at:
        return t

    if t and t.refresh_token:
        t2 = refresh_access_token(client_id, client_secret, t.refresh_token)
        save_tokens(token_path, t2)
        return t2

    raise RuntimeError("沒有 token 可用：請先跑一次互動式 OAuth（login -> code -> refresh_token）")


def interactive_oauth_flow(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    token_path: str,
    open_browser: bool = True,
) -> SchwabTokens:
    url = build_login_url(client_id, redirect_uri)
    if open_browser:
        webbrowser.open(url)

    # redirect_uri = http://127.0.0.1:8787/callback
    parsed = urllib.parse.urlparse(redirect_uri)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8787

    code = wait_for_auth_code(host, port, timeout_sec=180)
    t = exchange_code_for_refresh_token(client_id, client_secret, redirect_uri, code)
    save_tokens(token_path, t)
    return t
