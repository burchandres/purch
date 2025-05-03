from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    # db settings, defaults to local dev
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USERNAME: str = "default"
    DB_PASSWORD: str = "password"
    DB_TYPE: str = "postgres"
    DB_NAME: str = "pirch"
    # auth service settings
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Secret key for JWT signing
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings():
    """
    Get settings from environment variables or local.env file.
    """
    return Settings()
