"""
S3Storage — IStorageService implementation backed by AWS S3.

Used in production. Identical public interface to MinIOStorage (LSP):
swap the binding in the DI container and nothing else changes.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, override

import boto3
from botocore.exceptions import ClientError

from app.application.interfaces.storage_service import IStorageService
from app.core.config import get_configs
from app.domain.exceptions import StorageNotFoundError, StorageUploadError

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class S3Storage(IStorageService):
    """Object storage backed by AWS S3."""

    def __init__(self) -> None:
        configs = get_configs()
        self._bucket = configs.AWS_S3_BUCKET
        self._client: S3Client = boto3.client(
            "s3",
            region_name=configs.AWS_REGION,
            aws_access_key_id=configs.AWS_ACCESS_KEY_ID.get_secret_value(),
            aws_secret_access_key=configs.AWS_SECRET_ACCESS_KEY.get_secret_value(),
        )

    def _put_object(self, key: str, data: bytes, content_type: str) -> None:
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        except ClientError as exc:
            raise StorageUploadError(key, str(exc)) from exc

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

    def _make_presigned_url(self, key: str, expires_in: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    @override
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        await asyncio.to_thread(self._put_object, key, data, content_type)
        return await self.get_presigned_url(key)

    @override
    async def load_once(self, key: str) -> bytes:
        return await asyncio.to_thread(self._get_object_bytes, key)

    @override
    async def load_stream(self, key: str) -> AsyncGenerator[bytes, None]:
        chunks = await asyncio.to_thread(self._iter_chunks, key)
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
