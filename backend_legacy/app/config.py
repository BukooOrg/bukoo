from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://ecommerce:ecommerce123@localhost:5432/ecommerce_db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    CORS_ORIGINS: str = "http://localhost:3000"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    class Config:
        env_file = "backend_legacy/.env"
        env_file_encoding = "utf-8"


settings = Settings()
