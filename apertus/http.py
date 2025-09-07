from __future__ import annotations
import os
from typing import Any, Dict, Generator, Iterable, Optional

import httpx

from .errors import ApertusAPIError

DEFAULT_BASE_URL = "https://api.publicai.co"

class _BaseHTTP:
    def __init__(self, api_key: Optional[str] = None, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0):
        self.api_key = api_key or os.getenv("APERTUS_API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set APERTUS_API_KEY or pass api_key.")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

class SyncHTTP(_BaseHTTP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = httpx.Client(base_url=self.base_url, headers=self._headers(), timeout=self.timeout)

    def get(self, path: str) -> Dict[str, Any]:
        r = self._client.get(path)
        if r.status_code // 100 != 2:
            self._raise_api_error(r)
        return r.json()

    def post_json(self, path: str, json: Dict[str, Any]) -> Dict[str, Any]:
        r = self._client.post(path, json=json)
        if r.status_code // 100 != 2:
            self._raise_api_error(r)
        return r.json()

    def post_stream(self, path: str, json: Dict[str, Any]):
        with self._client.stream("POST", path, json=json) as resp:
            if resp.status_code // 100 != 2:
                body = resp.read().decode("utf-8", errors="ignore")
                self._raise_api_error_object(resp.status_code, body, url=str(resp.request.url), payload=json)
            for line in resp.iter_lines():
                if not line:
                    continue
                yield line

    def _raise_api_error(self, r: httpx.Response) -> None:
        try:
            data = r.json()
            message = data.get("error") or data.get("message") or r.text
        except Exception:
            message = r.text
            data = None
        raise ApertusAPIError(r.status_code, message, url=str(r.request.url), payload=data)

    def _raise_api_error_object(self, status: int, message: str, *, url: Optional[str], payload: Optional[dict]):
        raise ApertusAPIError(status, message, url=url, payload=payload)

class AsyncHTTP(_BaseHTTP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = httpx.AsyncClient(base_url=self.base_url, headers=self._headers(), timeout=self.timeout)

    async def get(self, path: str) -> Dict[str, Any]:
        r = await self._client.get(path)
        if r.status_code // 100 != 2:
            await self._raise_api_error(r)
        return r.json()

    async def post_json(self, path: str, json: Dict[str, Any]) -> Dict[str, Any]:
        r = await self._client.post(path, json=json)
        if r.status_code // 100 != 2:
            await self._raise_api_error(r)
        return r.json()

    async def post_stream(self, path: str, json: Dict[str, Any]):
        async with self._client.stream("POST", path, json=json) as resp:
            if resp.status_code // 100 != 2:
                body = await resp.aread()
                message = body.decode("utf-8", errors="ignore")
                await self._raise_api_error_object(resp.status_code, message, url=str(resp.request.url), payload=json)
            async for line in resp.aiter_lines():
                if not line:
                    continue
                yield line

    async def _raise_api_error(self, r: httpx.Response) -> None:
        try:
            data = r.json()
            message = data.get("error") or data.get("message") or r.text
        except Exception:
            message = r.text
            data = None
        raise ApertusAPIError(r.status_code, message, url=str(r.request.url), payload=data)

    async def _raise_api_error_object(self, status: int, message: str, *, url: Optional[str], payload: Optional[dict]):
        raise ApertusAPIError(status, message, url=url, payload=payload)
