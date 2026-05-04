"""
Application configuration.
Reads all settings from environment variables / .env file.
Implements the Singleton pattern via @lru_cache so Settings is
instantiated exactly once per process.
"""

from __future__ import annotations

import os
from enum import StrEnum
from functools import lru_cache

from pydantic import (
    AliasChoices,
    Field,
    PositiveInt,
    SecretStr,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import ObjectStorageType

from .util import size_to_bytes


class EnvironmentOption(StrEnum):
    LOCAL = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentConfig(BaseSettings):
    ENVIRONMENT: EnvironmentOption = Field(
        description="Deployment environment: development, staging, or production",
        default=EnvironmentOption.LOCAL,
    )


class AppConfig(BaseSettings):
    APP_DEBUG: bool = Field(
        description="Enable debug mode (verbose errors, auto-reload)",
        default=True,
    )
    APP_PORT: PositiveInt = Field(
        description="TCP port the application listens on",
        default=8000,
    )
    APP_NAME: str = Field(
        description="Human-readable application name shown in OpenAPI docs",
        default="FastAPI app",
    )
    APP_DESCRIPTION: str | None = Field(
        description="Application description shown in OpenAPI docs",
        default=None,
    )
    APP_VERSION: str | None = Field(
        description="Application version string shown in OpenAPI docs",
        default=None,
    )
    LICENSE_NAME: str | None = Field(
        description="License name shown in OpenAPI docs",
        default=None,
    )
    CONTACT_NAME: str | None = Field(
        description="Contact name shown in OpenAPI docs",
        default=None,
    )
    CONTACT_EMAIL: str | None = Field(
        description="Contact email shown in OpenAPI docs",
        default=None,
    )


class CORSConfig(BaseSettings):
    CORS_ORIGINS: list[str] = Field(
        description="List of allowed CORS origins; use ['*'] to allow all",
        default=["*"],
    )
    CORS_METHODS: list[str] = Field(
        description="List of allowed HTTP methods for CORS",
        default=["*"],
    )
    CORS_HEADERS: list[str] = Field(
        description="List of allowed HTTP headers for CORS",
        default=["*"],
    )


class SystemConfig(BaseSettings):
    DEFAULT_ADMIN_MAIL: str = Field(
        description="Default admin email",
        default="admin@gmail.com",
    )
    DEFAULT_ADMIN_FULL_NAME: str = Field(
        description="Default admin full name",
        default="Admin",
    )
    DEFAULT_ADMIN_PASSWORD: str = Field(
        description="Default admin password",
        default="Adm!n123",
    )


class SecurityConfig(BaseSettings):
    SECRET_KEY: SecretStr = Field(
        description="Secret key used to sign JWT tokens; must be kept private",
        default=SecretStr("secret-key"),
    )
    ALGORITHM: str = Field(
        description="JWT signing algorithm (e.g. HS256, RS256)",
        default="HS256",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: PositiveInt = Field(
        description="Lifetime of an access token in minutes",
        default=30,
    )
    REFRESH_TOKEN_EXPIRE_DAYS: PositiveInt = Field(
        description="Lifetime of a refresh token in days",
        default=7,
    )


class FileLoggerConfig(BaseSettings):
    FILE_LOG_MAX_BYTES: PositiveInt = Field(
        description="Maximum size in bytes of a single log file before rotation",
        default=10 * 1024 * 1024,
    )
    FILE_LOG_BACKUP_COUNT: PositiveInt = Field(
        description="Number of rotated log file backups to retain",
        default=5,
    )
    FILE_LOG_FORMAT_JSON: bool = Field(
        description="Emit file log entries as JSON instead of plain text",
        default=True,
    )
    FILE_LOG_LEVEL: str = Field(
        description="Minimum log level written to file (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        default="INFO",
    )

    # Include request ID, path, method, client host, and status code in the file log
    FILE_LOG_INCLUDE_REQUEST_ID: bool = Field(
        description="Include the request ID in each file log entry",
        default=True,
    )
    FILE_LOG_INCLUDE_PATH: bool = Field(
        description="Include the request path in each file log entry",
        default=True,
    )
    FILE_LOG_INCLUDE_METHOD: bool = Field(
        description="Include the HTTP method in each file log entry",
        default=True,
    )
    FILE_LOG_INCLUDE_CLIENT_HOST: bool = Field(
        description="Include the client host/IP in each file log entry",
        default=True,
    )
    FILE_LOG_INCLUDE_STATUS_CODE: bool = Field(
        description="Include the HTTP response status code in each file log entry",
        default=True,
    )


class ConsoleLoggerConfig(BaseSettings):
    CONSOLE_LOG_LEVEL: str = Field(
        description="Minimum log level written to stdout (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        default="INFO",
    )
    CONSOLE_LOG_FORMAT_JSON: bool = Field(
        description="Emit console log entries as JSON instead of plain text",
        default=False,
    )

    # Include request ID, path, method, client host, and status code in the file log
    CONSOLE_LOG_INCLUDE_REQUEST_ID: bool = Field(
        description="Include the request ID in each console log entry",
        default=False,
    )
    CONSOLE_LOG_INCLUDE_PATH: bool = Field(
        description="Include the request path in each console log entry",
        default=False,
    )
    CONSOLE_LOG_INCLUDE_METHOD: bool = Field(
        description="Include the HTTP method in each console log entry",
        default=False,
    )
    CONSOLE_LOG_INCLUDE_CLIENT_HOST: bool = Field(
        description="Include the client host/IP in each console log entry",
        default=False,
    )
    CONSOLE_LOG_INCLUDE_STATUS_CODE: bool = Field(
        description="Include the HTTP response status code in each console log entry",
        default=False,
    )


class DatabaseConfig(BaseSettings):
    pass


class PostgresConfig(DatabaseConfig):
    POSTGRES_USER: str = Field(
        description="PostgreSQL username",
        default="postgres",
    )
    POSTGRES_PASSWORD: str = Field(
        description="PostgreSQL password",
        default="postgres",
    )
    POSTGRES_SERVER: str = Field(
        description="PostgreSQL server hostname or IP",
        default="localhost",
    )
    POSTGRES_PORT: PositiveInt = Field(
        description="PostgreSQL server port",
        default=5432,
    )
    POSTGRES_DB: str = Field(
        description="PostgreSQL database name",
        default="postgres",
    )
    POSTGRES_SYNC_PREFIX: str = Field(
        description="URL scheme prefix for synchronous SQLAlchemy connections",
        default="postgresql://",
    )
    POSTGRES_ASYNC_PREFIX: str = Field(
        description="URL scheme prefix for async SQLAlchemy connections (asyncpg driver)",
        default="postgresql+asyncpg://",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def POSTGRES_URI(self) -> str:
        credentials = f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
        location = f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return f"{credentials}@{location}"


class ObjectStorageConfig(BaseSettings):
    STORAGE_TYPE: ObjectStorageType = Field(
        description="Type of storage to use.Options: 'minio', s3",
        default=ObjectStorageType.MINIO,
    )
    STREAM_CHUNK_SIZE: str = Field(
        description="Chunk size used by load_stream"
        "Default is 8MB that is matched with the S3 multipart minimum",
        default="8mb",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def STREAM_CHUNK_SIZE_BYTES(self) -> int:
        default_size_bytes = 8 * 1024**2  # 8mb

        size_bytes = size_to_bytes(self.STREAM_CHUNK_SIZE) or default_size_bytes

        return max(default_size_bytes, size_bytes)


class MinioConfig(BaseSettings):
    MINIO_ENDPOINT: str = Field(
        description="MinIO server endpoint in host:port format",
        default="localhost:9000",
    )
    MINIO_ACCESS_KEY: str = Field(
        description="MinIO access key (username)",
        default="minioadmin",
    )
    MINIO_SECRET_KEY: str = Field(
        description="MinIO secret key (password)",
        default="minioadmin",
    )
    MINIO_BUCKET: str = Field(
        description="Default MinIO bucket name used by the application",
        default="bookstore",
    )
    MINIO_USE_SSL: bool = Field(
        description="Use TLS/SSL when connecting to MinIO",
        default=False,
    )
    MINIO_PUBLIC: bool = Field(
        description="MinIO public access boolean flag",
        default=True,
    )


class S3StorageConfig(BaseSettings):
    AWS_S3_BUCKET: str = Field(
        description="AWS S3 bucket name for object storage",
        default="",
    )
    AWS_REGION: str = Field(
        description="AWS region where the S3 bucket is located",
        default="ap-southeast-1",
    )
    AWS_ACCESS_KEY_ID: SecretStr = Field(
        description="AWS access key ID for S3 authentication",
        default=SecretStr("aws-access-key-id"),
    )
    AWS_SECRET_ACCESS_KEY: SecretStr = Field(
        description="AWS secret access key for S3 authentication",
        default=SecretStr("aws-secret-access-key"),
    )


class GoogleOAuthConfig(BaseSettings):
    GOOGLE_CLIENT_ID: SecretStr = Field(
        description="Google OAuth 2.0 client ID",
        default=SecretStr("google-client-id"),
    )
    GOOGLE_CLIENT_SECRET: SecretStr = Field(
        description="Google OAuth 2.0 client secret",
        default=SecretStr("google-client-secret"),
    )
    GOOGLE_REDIRECT_URI: str = Field(
        description="OAuth 2.0 redirect URI registered with Google; must match exactly",
        validation_alias=AliasChoices(
            "GOOGLE_REDIRECT_URI", "GOOGLE_OAUTH_REDIRECT_URI"
        ),
        default="http://localhost:8000/api/v1/auth/google/callback",
    )


class RedisConfig(BaseSettings):
    BROKER_REDIS_URL: str = Field(
        description="Redis broker URL used by Celery",
        default="redis://localhost:6379/0",
    )
    CACHE_REDIS_URL: str = Field(
        description="Redis URL for the application cache (token blocklist, OTP storage, etc.)",
        default="redis://localhost:6379/1",
    )


class MailConfig(BaseSettings):
    SMTP_HOST: str = Field(
        description="SMTP server hostname",
        default="localhost",
    )
    SMTP_PORT: PositiveInt = Field(
        description="SMTP server port (e.g. 25, 465, 587, 1025)",
        default=1025,
    )
    SMTP_USERNAME: str = Field(
        description="SMTP authentication username; leave empty to skip auth",
        default="",
    )
    SMTP_PASSWORD: str = Field(
        description="SMTP authentication password; leave empty to skip auth",
        default="",
    )
    SMTP_FROM: str = Field(
        description="Sender address used in the From header of outgoing emails",
        default="noreply@bukoo.local",
    )
    SMTP_TLS: bool = Field(
        description="Enable STARTTLS when connecting to the SMTP server",
        default=False,
    )


class Config(
    EnvironmentConfig,
    AppConfig,
    CORSConfig,
    SystemConfig,
    SecurityConfig,
    FileLoggerConfig,
    ConsoleLoggerConfig,
    PostgresConfig,
    ObjectStorageConfig,
    MinioConfig,
    S3StorageConfig,
    GoogleOAuthConfig,
    RedisConfig,
    MailConfig,
):
    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "..", "..", ".env"
        ),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_configs() -> Config:
    """Return the singleton Settings instance."""
    return Config()
