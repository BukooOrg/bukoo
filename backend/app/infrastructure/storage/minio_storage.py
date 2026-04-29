"""
MinIOStorage — implements IStorageService using MinIO (boto3-compatible).
Used in development. Substitutable with S3Storage in production (LSP).
"""

from __future__ import annotations

from typing import override

import boto3
from botocore.exceptions import ClientError

from app.application.interfaces.storage_service import IStorageService
from app.core.config import get_configs
from app.domain.exceptions import StorageUploadError


class MinIOStorage(IStorageService):
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

    @override
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        except ClientError as exc:
            raise StorageUploadError(key, str(exc)) from exc
        return await self.get_presigned_url(key)

    @override
    async def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    @override
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        url: str = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url
