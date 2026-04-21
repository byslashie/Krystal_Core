# brokers/schwab_api.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


# ------------------------------------------------------------
# Token storage
# ------------------------------------------------------------
DEFAULT_TOKEN_PATH = Path(__file__).resolve().parent.parent / "secrets" / "schwab_token.json"


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def load_token(token_path: Path = DEFAULT_TOKEN_PATH) -> Optional[Dict[str, Any]]:
    try:
        if token_path.exists():
            return json.loads(token_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def save_token(token: Dict[str, Any], token_path: Path = DEFAULT_TOKEN_PATH) -> None:
    _ensure_parent(token_path)
    token_path.write_text(json.dumps(token, ensure_ascii=False, indent=2), encoding="utf-8")


def has_valid_token(token: Optional[Dict[str, Any]]) -> bool:
    """
    先用簡單規則判定：有 access_token 且未過期（如果有 expires_at）
    """
    if not token:
        return False
    at = str(token.get("access_token", "")).strip()
    if not at:
        return False

    exp = token.get("expires_at")
    if exp is None:
        # 沒存過期時間：先視為可用（之後你接 refresh 再嚴格）
        return True

    try:
        exp_ts = float(exp)
        now_ts = datetime.now(tz=timezone.utc).timestamp()
        return now_ts < exp_ts - 30  # 提前 30 秒視為過期
    except Exception:
        return True


# ------------------------------------------------------------
# OAuth skeleton (not fully wired until Schwab approve)
# ------------------------------------------------------------
@dataclass
class SchwabConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    auth_base: str = "https://api.schwabapi.com/v1/oauth/authorize"
    token_url: str = "https://api.schwabapi.com/v1/oauth/token"
    scope: str = "accounts positions"  # 先預設，之後可依 Schwab 文件調整


def load_config_from_env() -> SchwabConfig:
    client_id = os.getenv("SCHWAB_CLIENT_ID", "").strip()
    client_secret = os.getenv("SCHWAB_CLIENT_SECRET", "").strip()
    redirect_uri = os.getenv("SCHWAB_REDIRECT_URI", "").strip()

    return SchwabConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=os.getenv("SCHWAB_SCOPE", "accounts positions").strip() or "accounts positions",
    )


def is_schwab_enabled() -> bool:
    """
    啟用條件（你可改嚴格一點）：
    - env 裡至少要有 client_id / redirect_uri
    - 有 token 且有效（目前先用本地 token 檔判斷）
    """
    cfg = load_config_from_env()
    if not cfg.client_id or not cfg.redirect_uri:
        return False
    tok = load_token()
    return has_valid_token(tok)


def get_authorize_url(state: str = "krystal") -> str:
    """
    先產出授權網址（真正能用要等 Schwab 產品開通）
    """
    cfg = load_config_from_env()
    if not cfg.client_id or not cfg.redirect_uri:
        raise RuntimeError("SCHWAB_CLIENT_ID / SCHWAB_REDIRECT_URI 未設定，無法產生 authorize URL")

    # response_type / client_id / redirect_uri / scope / state
    # scope 實際要以 Schwab 文件為準，先留骨架
    from urllib.parse import urlencode

    params = {
        "response_type": "code",
        "client_id": cfg.client_id,
        "redirect_uri": cfg.redirect_uri,
        "scope": cfg.scope,
        "state": state,
    }
    return f"{cfg.auth_base}?{urlencode(params)}"


# ------------------------------------------------------------
# API Calls
# 🔑 需要 SCHWAB_CLIENT_ID / SCHWAB_CLIENT_SECRET / SCHWAB_REDIRECT_URI
#    見 schwab_oauth.py 進行 OAuth 認證
# 🕐 首次使用時執行：
#    from brokers.schwab_oauth import interactive_oauth_flow
#    tokens = interactive_oauth_flow(client_id, client_secret, redirect_uri, token_path)
# 📌 之後的每次調用會自動 refresh token
# ------------------------------------------------------------

def get_valid_token(token_path: Path = DEFAULT_TOKEN_PATH) -> Optional[str]:
    """
    獲取有效的 access_token（自動 refresh）

    Returns:
        access_token 字符串，或 None（未認證）
    """
    try:
        from brokers.schwab_oauth import get_valid_access_token, load_tokens

        cfg = load_config_from_env()
        if not cfg.client_id or not cfg.client_secret:
            return None

        tokens = get_valid_access_token(cfg.client_id, cfg.client_secret, str(token_path))
        return tokens.access_token
    except Exception:
        return None


def _force_refresh_token(token_path: Path = DEFAULT_TOKEN_PATH) -> Optional[str]:
    """強制用 refresh_token 換新的 access_token（不管舊的是否還沒過期）"""
    try:
        from brokers.schwab_oauth import load_tokens, refresh_access_token, save_tokens
        cfg = load_config_from_env()
        if not cfg.client_id or not cfg.client_secret:
            return None
        t = load_tokens(str(token_path))
        if not t or not t.refresh_token:
            return None
        t2 = refresh_access_token(cfg.client_id, cfg.client_secret, t.refresh_token)
        save_tokens(str(token_path), t2)
        return t2.access_token
    except Exception:
        return None


def _do_http(url: str, method: str, access_token: str) -> "requests.Response":
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    if method == "GET":
        return requests.get(url, headers=headers, timeout=30)
    headers["Content-Type"] = "application/json"
    return requests.post(url, headers=headers, timeout=30)


def _api_request(endpoint: str, method: str = "GET", token_path: Path = DEFAULT_TOKEN_PATH) -> Optional[Dict[str, Any]]:
    """
    統一的 Schwab API 請求函數（遇到 400/401 會自動 refresh token 重試一次）

    Args:
        endpoint: API 端點路徑（例如 "/trader/v1/accounts"）
        method: HTTP 方法（GET / POST）
        token_path: token 檔案路徑
    """
    access_token = get_valid_token(token_path)
    if not access_token:
        return None

    url = f"https://api.schwabapi.com{endpoint}"

    for attempt in (0, 1):
        r = _do_http(url, method, access_token)
        if r.status_code == 200:
            return r.json()

        # 401 或 400（Schwab 把 token 問題包成 400）→ 嘗試 refresh 一次
        should_retry = r.status_code in (400, 401) and attempt == 0
        if should_retry:
            new_token = _force_refresh_token(token_path)
            if new_token:
                access_token = new_token
                continue

        # 不可重試：解析 body 決定錯誤類型
        try:
            body = r.json()
            errors = body.get("errors", [])
            if errors and errors[0].get("status") == 500:
                raise RuntimeError(f"Schwab 伺服器錯誤 (server 500): {errors[0].get('title', 'Internal Server Error')}")
        except (ValueError, KeyError, IndexError):
            pass

        r.raise_for_status()
        return r.json()

    return None


def get_schwab_accounts(token_path: Path = DEFAULT_TOKEN_PATH) -> Optional[Dict[str, Any]]:
    """
    獲取 Schwab 帳戶列表

    Returns:
        {
            "accounts": [
                {
                    "accountNumber": "...",
                    "accountType": "...",
                    "nickname": "...",
                    ...
                },
                ...
            ]
        }
    """
    return _api_request("/trader/v1/accounts?fields=positions", "GET", token_path)


def get_schwab_account_details(account_hash: str, token_path: Path = DEFAULT_TOKEN_PATH) -> Optional[Dict[str, Any]]:
    """
    獲取特定帳戶詳情（含持倉）

    Args:
        account_hash: 帳戶 hash（from get_schwab_accounts）

    Returns:
        帳戶詳細信息
    """
    return _api_request(f"/trader/v1/accounts/{account_hash}?fields=positions", "GET", token_path)


def get_schwab_positions(account_hash: str = None, token_path: Path = DEFAULT_TOKEN_PATH) -> List[Dict[str, Any]]:
    """
    獲取 Schwab 開倉持倉

    Args:
        account_hash: 帳戶 hash。若為 None，則從第一個帳戶拉取
        token_path: token 檔案路徑

    Returns:
        [
            {
                "symbol": "AAPL",
                "quantity": 10,
                "averagePrice": 150.25,
                "marketValue": 1502.50,
                "positionValue": 1502.50,
                "costBasis": 1502.50,
                ...
            },
            ...
        ]
    """
    # 若未指定帳戶，先拿第一個
    if not account_hash:
        accounts_resp = get_schwab_accounts(token_path)
        if not accounts_resp or not accounts_resp.get("accounts"):
            return []
        account_hash = accounts_resp["accounts"][0].get("accountNumber")

    if not account_hash:
        return []

    details = get_schwab_account_details(account_hash, token_path)
    if not details:
        return []

    # Schwab 的帳戶詳情會包含 positions 陣列
    return details.get("positions", [])


def get_schwab_all_positions(token_path: Path = DEFAULT_TOKEN_PATH) -> List[Dict[str, Any]]:
    """
    獲取所有帳戶的開倉持倉（合併）

    Returns:
        所有帳戶的持倉列表
    """
    accounts_resp = get_schwab_accounts(token_path)
    if not accounts_resp or not accounts_resp.get("accounts"):
        return []

    all_positions = []
    for account in accounts_resp["accounts"]:
        account_hash = account.get("accountNumber")
        try:
            positions = get_schwab_positions(account_hash, token_path)
            all_positions.extend(positions)
        except Exception as e:
            import logging
            logging.warning(f"獲取帳戶 {account_hash} 持倉失敗: {e}")

    return all_positions


def get_schwab_balances(account_hash: str = None, token_path: Path = DEFAULT_TOKEN_PATH) -> Optional[Dict[str, Any]]:
    """
    獲取帳戶餘額與資產信息

    Args:
        account_hash: 帳戶 hash（若為 None 則用第一個帳戶）

    Returns:
        {
            "accountNumber": "...",
            "balances": {
                "cash": { "value": ..., "currency": "USD" },
                "stocks": { "value": ..., "currency": "USD" },
                "bonds": { "value": ..., "currency": "USD" },
                "options": { "value": ..., "currency": "USD" },
                ...
            },
            ...
        }
    """
    if not account_hash:
        accounts_resp = get_schwab_accounts(token_path)
        if not accounts_resp or not accounts_resp.get("accounts"):
            return None
        account_hash = accounts_resp["accounts"][0].get("accountNumber")

    if not account_hash:
        return None

    return _api_request(f"/trader/v1/accounts/{account_hash}/balances", "GET", token_path)


def get_schwab_account_hash(token_path: Path = DEFAULT_TOKEN_PATH) -> Optional[str]:
    """取得帳戶的 hashValue（交易歷史 API 需要用 hash 而非 accountNumber）"""
    result = _api_request("/trader/v1/accounts/accountNumbers", "GET", token_path)
    if result and isinstance(result, list) and len(result) > 0:
        return result[0].get("hashValue")
    return None


def get_schwab_transactions(
    start_date: str = None,
    end_date: str = None,
    token_path: Path = DEFAULT_TOKEN_PATH,
) -> List[Dict[str, Any]]:
    """
    取得 Schwab 交易歷史，並整理成統一格式。

    Args:
        start_date: 起始日 YYYY-MM-DD（預設 90 天前）
        end_date: 結束日 YYYY-MM-DD（預設今天）

    Returns:
        [
            {
                'tradeDate': '2026-04-14',
                'symbol': 'KO',
                'description': 'Coca-Cola Co',
                'side': 'SELL',
                'shares': 4,
                'price': 76.475,
                'amount': 305.90,
                'fee': 0.01,
                'netAmount': 305.89,
                'currency': 'USD',
                'orderId': '...',
                'positionEffect': 'CLOSING',
                'activityId': 123456,
            },
            ...
        ]
    """
    account_hash = get_schwab_account_hash(token_path)
    if not account_hash:
        return []

    if not start_date:
        start_date = (datetime.now(tz=timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

    endpoint = (
        f"/trader/v1/accounts/{account_hash}/transactions"
        f"?types=TRADE&startDate={start_date}T00:00:00.000Z&endDate={end_date}T23:59:59.000Z"
    )
    raw = _api_request(endpoint, "GET", token_path)
    if not raw or not isinstance(raw, list):
        return []

    trades = []
    for tx in raw:
        items = tx.get("transferItems", [])
        fees = sum(abs(fi.get("cost", 0)) for fi in items if fi.get("feeType"))
        for item in items:
            inst = item.get("instrument", {})
            if inst.get("assetType") == "CURRENCY":
                continue
            sym = inst.get("symbol", "")
            amt = float(item.get("amount", 0))
            if amt == 0:
                continue
            price = float(item.get("price", 0))
            side = "BUY" if amt > 0 else "SELL"
            shares = abs(amt)
            amount = round(shares * price, 2)
            trades.append({
                "tradeDate": tx.get("tradeDate", "")[:10],
                "symbol": sym,
                "description": inst.get("description", ""),
                "side": side,
                "shares": shares,
                "price": price,
                "amount": amount,
                "fee": round(fees, 2),
                "netAmount": round(float(tx.get("netAmount", 0)), 2),
                "currency": "USD",
                "orderId": str(tx.get("orderId", "")),
                "positionEffect": item.get("positionEffect", ""),
                "activityId": tx.get("activityId"),
            })
    return trades


