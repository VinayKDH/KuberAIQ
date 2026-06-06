"""Local filesystem blob storage (mock adapter)."""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

from app.core.config import settings


class LocalBlobStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self._base = Path(base_dir or settings.local_blob_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    async def upload(self, path: str, data: bytes, content_type: str) -> str:
        full = self._base / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)
        return path

    async def get_signed_url(self, path: str, ttl_seconds: int) -> str:
        return f"file://{quote(str(self._base / path))}?ttl={ttl_seconds}"

    async def download(self, path: str) -> bytes:
        return (self._base / path).read_bytes()
