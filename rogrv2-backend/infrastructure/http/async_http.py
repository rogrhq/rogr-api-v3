from __future__ import annotations
import httpx
from typing import Optional

def client(timeout: float = 10.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=True, timeout=httpx.Timeout(timeout, connect=5.0))

async def get_text(url: str, *, client: Optional[httpx.AsyncClient] = None, timeout: float = 10.0) -> str:
    close = False
    if client is None:
        client = httpx.AsyncClient(follow_redirects=True, timeout=httpx.Timeout(timeout, connect=5.0))
        close = True
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text or ""
    finally:
        if close:
            await client.aclose()