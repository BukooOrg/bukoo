"""
MinIOStorage — IStorageService implementation backed by MinIO.

Used in development via a boto3-compatible S3 endpoint.
Swap for S3Storage in production without changing any call-sites (LSP).
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import override

import boto3
from botocore.exceptions import ClientError

from app.application.interfaces.storage_service import IStorageService
from app.core.config import get_configs
from app.domain.exceptions import StorageNotFoundError, StorageUploadError


class MinIOStorage(IStorageService):
    """Object storage backed by a local MinIO instance."""

    def __init__(self) -> None:
        configs = get_configs()
        self._bucket = configs.MINIO_BUCKET
        protocol = "https" if configs.MINIO_USE_SSL else "http"
        self._client = boto3.client(
            "s3",
            endpoint_url=f"{protocol}://{configs.MINIO_ENDPOINT}",
            aws_access_key_id=configs.MINIO_ACCESS_KEY,
            aws_secret_access_key=configs.MINIO_SECRET_KEY,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self._bucket)

    def _put_object(self, key: str, data: bytes, content_type: str) -> None:
        try:
            self._client.put_object(
                Bucket=self._bucket, Key=key, Body=data, ContentType=content_type
            )
        except ClientError as exc:
            raise StorageUploadError(key, str(exc)) from exc

    def _make_presigned_url(self, key: str, expires_in: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def _get_object_bytes(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in ("NoSuchKey", "404"):
                raise StorageNotFoundError(key) from exc
            raise StorageUploadError(key, str(exc)) from exc

    def _iter_chunks(self, key: str) -> list[bytes]:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in ("NoSuchKey", "404"):
                raise StorageNotFoundError(key) from exc
            raise StorageUploadError(key, str(exc)) from exc

        chunks: list[bytes] = []
        body = response["Body"]
        configs = get_configs()

        while True:
            chunk = body.read(configs.STREAM_CHUNK_SIZE_BYTES)
            if not chunk:
                break
            chunks.append(chunk)

        return chunks

    def _head_object(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False

    def _delete_object(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    @override
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        await asyncio.to_thread(self._put_object, key, data, content_type)
        return await self.get_presigned_url(key)

    @override
    async def load_once(self, key: str) -> bytes:
        return await asyncio.to_thread(self._get_object_bytes, key)

    @override
    async def load_stream(self, key: str) -> AsyncGenerator[bytes, None]:
        chunks: list[bytes] = await asyncio.to_thread(self._iter_chunks, key)
        for chunk in chunks:
            yield chunk

    @override
    async def exists(self, key: str) -> bool:
        return await asyncio.to_thread(self._head_object, key)

    @override
    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._delete_object, key)

    @override
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return await asyncio.to_thread(self._make_presigned_url, key, expires_in)
