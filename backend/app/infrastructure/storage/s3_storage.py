"""
S3Storage — implements IStorageService using AWS S3.
Used in production. Identical interface to MinIOStorage (LSP).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import boto3
from botocore.exceptions import ClientError

from app.application.interfaces.storage_service import IStorageService
from app.core.config import get_configs
from app.domain.exceptions import StorageUploadError

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class S3Storage(IStorageService):
    def __init__(self) -> None:
        configs = get_configs()
        self._bucket = configs.AWS_S3_BUCKET
        self._client: S3Client = boto3.client(
            "s3",
            region_name=configs.AWS_REGION,
            aws_access_key_id=configs.AWS_ACCESS_KEY_ID.get_secret_value(),
            aws_secret_access_key=configs.AWS_SECRET_ACCESS_KEY.get_secret_value(),
        )

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
