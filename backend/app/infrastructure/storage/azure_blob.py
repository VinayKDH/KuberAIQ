"""Azure Blob Storage adapter."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from azure.storage.blob import BlobSasPermissions, ContentSettings, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient

from app.core.config import settings
from app.core.errors import ValidationAppError


class AzureBlobStorage:
    def __init__(self) -> None:
        if not settings.azure_blob_connection_string:
            raise ValidationAppError("Azure Blob connection string is not configured")
        self._client = BlobServiceClient.from_connection_string(
            settings.azure_blob_connection_string
        )
        self._container = settings.azure_blob_container

    async def upload(self, path: str, data: bytes, content_type: str) -> str:
        blob = self._client.get_blob_client(container=self._container, blob=path)
        await blob.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )
        return path

    async def get_signed_url(self, path: str, ttl_seconds: int) -> str:
        blob = self._client.get_blob_client(container=self._container, blob=path)
        account_name = self._client.account_name
        credential = self._client.credential
        account_key = getattr(credential, "account_key", None)
        if not account_key:
            raise ValidationAppError("Blob account key unavailable for signed URL generation")
        sas = generate_blob_sas(
            account_name=account_name,
            container_name=self._container,
            blob_name=path,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
        )
        return f"{blob.url}?{sas}"

    async def download(self, path: str) -> bytes:
        blob = self._client.get_blob_client(container=self._container, blob=path)
        stream = await blob.download_blob()
        return await stream.readall()
