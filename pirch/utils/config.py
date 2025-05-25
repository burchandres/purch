import plaid

from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import SecretStr

from pirch.utils.financial import PlaidEnvs


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
    # PLAID ENV (temp, to be moved elsewhere probably)
    PLAID_CLIENT_ID: str
    PLAID_SECRET: SecretStr
    PLAID_ENV: PlaidEnvs
    PLAID_PRODUCTS: str
    PLAID_COUNTRY_CODES: str
    PLAID_REDIRECT_URI: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_plaid_host(self):
        if self.PLAID_ENV == PlaidEnvs.sandbox:
            return plaid.Environment.Sandbox
        return plaid.Environment.Production

    def get_plaid_products(self):
        return self.PLAID_PRODUCTS.split(",")


@lru_cache
def get_settings():
    """
    Get settings from environment variables or local.env file.
    """
    return Settings()
