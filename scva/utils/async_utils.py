"""
Asynchronous HTTP helpers with rate-limiting, headers, and retry logic.
"""
from __future__ import annotations

import asyncio
import aiohttp
from typing import Any, Optional

DEFAULT_HEADERS = {
    "User-Agent": "SCVA/1.0 (Scientific Citation Verification Agent; mailto:scva-polite@research-community.org)",
    "Accept": "application/json",
}


async def fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    headers: Optional[dict[str, str]] = None,
    params: Optional[dict[str, Any]] = None,
    retries: int = 3,
    backoff: float = 1.5,
) -> Optional[dict[str, Any]]:
    """Fetch JSON from URL with exponential backoff on transient errors."""
    req_headers = {**DEFAULT_HEADERS, **(headers or {})}

    for attempt in range(retries):
        try:
            async with session.get(url, headers=req_headers, params=params, timeout=15) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status in (404, 400):
                    return None
                elif resp.status in (429, 500, 502, 503, 504):
                    await asyncio.sleep(backoff * (attempt + 1))
                else:
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            if attempt < retries - 1:
                await asyncio.sleep(backoff * (attempt + 1))
            else:
                return None
    return None


async def fetch_bytes(
    session: aiohttp.ClientSession,
    url: str,
    headers: Optional[dict[str, str]] = None,
    retries: int = 2,
) -> Optional[bytes]:
    """Fetch raw bytes (e.g. PDF) from URL."""
    req_headers = {**DEFAULT_HEADERS, **(headers or {})}
    req_headers.pop("Accept", None)

    for attempt in range(retries):
        try:
            async with session.get(url, headers=req_headers, timeout=20) as resp:
                if resp.status == 200:
                    return await resp.read()
                elif resp.status in (429, 500, 502, 503):
                    await asyncio.sleep(1.0 * (attempt + 1))
        except (aiohttp.ClientError, asyncio.TimeoutError):
            pass
    return None
