from __future__ import annotations

import base64
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict
from urllib.parse import urljoin

import requests


TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
API_BASE_URL = "https://api.schwabapi.com"


class SchwabClientError(RuntimeError):
    pass


@dataclass
class SchwabTokenState:
    access_token: str = ""
    refresh_token: str = ""
    expires_at_epoch: float = 0.0

    @property
    def is_valid(self) -> bool:
        return bool(self.access_token) and time.time() < (self.expires_at_epoch - 60.0)


class SchwabClient:
    """
    Minimal Schwab API client for market-data dashboard usage.

    Auth strategy:
    - If SCHWAB_ACCESS_TOKEN exists and still valid in-memory, use it.
    - Else refresh with SCHWAB_CLIENT_ID + SCHWAB_CLIENT_SECRET + SCHWAB_REFRESH_TOKEN.
    """

    def __init__(
        self,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        access_token: str | None = None,
        timeout_seconds: int = 20,
    ) -> None:
        self.client_id = (client_id or os.getenv("SCHWAB_CLIENT_ID", "")).strip()
        self.client_secret = (client_secret or os.getenv("SCHWAB_CLIENT_SECRET", "")).strip()
        self.timeout_seconds = timeout_seconds
        self._lock = threading.Lock()
        self._session = requests.Session()
        self._token = SchwabTokenState(
            access_token=(access_token or os.getenv("SCHWAB_ACCESS_TOKEN", "")).strip(),
            refresh_token=(refresh_token or os.getenv("SCHWAB_REFRESH_TOKEN", "")).strip(),
            expires_at_epoch=0.0,
        )

    def _basic_auth_header(self) -> str:
        if not self.client_id or not self.client_secret:
            raise SchwabClientError(
                "SCHWAB_CLIENT_ID and SCHWAB_CLIENT_SECRET are required to refresh Schwab access token."
            )
        token = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("ascii")
        return f"Basic {token}"

    def _refresh_access_token(self) -> None:
        if not self._token.refresh_token:
            raise SchwabClientError(
                "SCHWAB_REFRESH_TOKEN is missing. Set SCHWAB_ACCESS_TOKEN for temporary read-only usage "
                "or configure refresh credentials."
            )

        form = {
            "grant_type": "refresh_token",
            "refresh_token": self._token.refresh_token,
        }
        headers = {
            "Authorization": self._basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = self._session.post(TOKEN_URL, data=form, headers=headers, timeout=self.timeout_seconds)
        if response.status_code != 200:
            raise SchwabClientError(
                f"Schwab token refresh failed: HTTP {response.status_code} - {response.text[:300]}"
            )

        payload = response.json()
        access_token = (payload.get("access_token") or payload.get("token") or "").strip()
        if not access_token:
            raise SchwabClientError("Schwab token refresh response missing access token.")

        expires_in = int(payload.get("expires_in", payload.get("expiresIn", 1800)))
        new_refresh_token = (payload.get("refresh_token") or "").strip()
        if new_refresh_token:
            self._token.refresh_token = new_refresh_token

        self._token.access_token = access_token
        self._token.expires_at_epoch = time.time() + max(300, expires_in)

    def get_access_token(self, *, force_refresh: bool = False) -> str:
        with self._lock:
            if not force_refresh and self._token.is_valid:
                return self._token.access_token

            if self._token.access_token and not force_refresh and self._token.expires_at_epoch == 0:
                # Access token provided without expiry metadata. Use until a request returns 401.
                return self._token.access_token

            self._refresh_access_token()
            return self._token.access_token

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Dict[str, Any] | None = None,
        json_payload: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        url = urljoin(API_BASE_URL, path)

        token = self.get_access_token()
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        response = self._session.request(
            method=method,
            url=url,
            params=params,
            json=json_payload,
            headers=headers,
            timeout=self.timeout_seconds,
        )
        if response.status_code == 401:
            # One forced refresh retry.
            token = self.get_access_token(force_refresh=True)
            headers["Authorization"] = f"Bearer {token}"
            response = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json_payload,
                headers=headers,
                timeout=self.timeout_seconds,
            )

        if response.status_code >= 400:
            raise SchwabClientError(f"Schwab API error {response.status_code}: {response.text[:400]}")

        if not response.content:
            return {}
        return response.json()

    def get_quotes(self, symbols: list[str]) -> Dict[str, Any]:
        if not symbols:
            return {}
        joined_symbols = ",".join(symbols)
        return self._request("GET", "/marketdata/v1/quotes", params={"symbols": joined_symbols})

    def get_option_chain(
        self,
        *,
        symbol: str,
        contract_type: str = "ALL",
        strike_count: int = 60,
        include_quotes: bool = True,
        strategy: str = "SINGLE",
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "symbol": symbol,
            "contractType": contract_type,
            "strikeCount": strike_count,
            "includeQuotes": str(include_quotes).lower(),
            "strategy": strategy,
        }
        return self._request("GET", "/marketdata/v1/chains", params=params)

    def get_accounts_numbers(self) -> Dict[str, Any]:
        return self._request("GET", "/trader/v1/accounts/accountNumbers")
