"""Blob storage port."""
from __future__ import annotations

from typing import Protocol


class StoragePort(Protocol):
    async def upload(self, path: str, data: bytes, content_type: str) -> str: ...

    async def get_signed_url(self, path: str, ttl_seconds: int) -> str: ...

    async def download(self, path: str) -> bytes: ...
