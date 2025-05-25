import plaid

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import SecretStr
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

from pirch.utils.finance import PlaidEnvs


class Settings(BaseSettings):
    PRODUCT_NAME: str = "Pirch"
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
    PLAID_REDIRECT_URI: str | None
    PLAID_LANGUAGE: str = "en"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_plaid_host(self):
        """Returns the appropriate Plaid Enum Environment variable based on PLAID_ENV value."""
        if self.PLAID_ENV == PlaidEnvs.sandbox:
            return plaid.Environment.Sandbox
        return plaid.Environment.Production

    def get_plaid_products(self):
        """Returns a list of the products in a Plaid acceptable format defined in PLAID_PRODUCTS"""
        return list(map(lambda p: Products(p), self.PLAID_PRODUCTS.split(",")))

    def get_plaid_country_codes(self):
        return list(
            map(
                lambda cc: CountryCode(cc.lstrip()), self.PLAID_COUNTRY_CODES.split(",")
            )
        )


@lru_cache
def get_settings():
    """
    Get settings from .env file file.
    """
    return Settings()
