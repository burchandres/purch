import plaid

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

from purch.core.finance import PlaidEnvs


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    PRODUCT_NAME: str = Field(default="Purch", description="Name of the finance app")
    # postgres settings, defaults to local dev
    POSTGRES_HOST: str = Field(
        default="localhost", description="postgres database host"
    )
    POSTGRES_PORT: int = Field(default=5432, description="postgres database port")
    POSTGRES_USERNAME: str = Field(
        default="postgres", description="postgres database username"
    )
    POSTGRES_PASSWORD: SecretStr = Field(
        default="password", description="postgres database password"
    )
    POSTGRES_DATABASE: str = Field(
        default="purch",
        description="name of the database folder all tables will be stored in",
    )
    # redis settings, defaults to local dev
    REDIS_HOST: str = Field(default="localhost", description="redis database host")
    REDIS_PORT: int = Field(default=6379, description="redis database port")
    REDIS_USERNAME: str = Field(default="redis", description="redis database username")
    REDIS_PASSWORD: SecretStr = Field(
        default="password", description="redis database password"
    )
    REDIS_DATABASE: int = Field(
        default=0,
        description="which of the 16 redis databases (numbered 0-15) to connect to"
    )
    # auth service settings
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="time, in minutes, the jwt lasts per user"
    )
    # Secret key for JWT signing
    SECRET_KEY: SecretStr = Field(description="secret key used for password encryption")
    ALGORITHM: str = Field(
        default="HS256",
        description="hashing algorithm used with secret_key for password encryption",
    )
    # PLAID ENV
    PLAID_CLIENT_ID: str
    PLAID_SECRET: SecretStr
    PLAID_ENV: PlaidEnvs = Field(
        default=PlaidEnvs.sandbox.value,
        description="when sandbox is set no real data can be pulled, primarily for testing. Production env is for deployment and real use",
    )
    PLAID_PRODUCTS: str
    PLAID_COUNTRY_CODES: str
    PLAID_REDIRECT_URI: str | None = Field(
        default="http://localhost:5379/dashboard",
        description="Required for OAuth institutions upon successful user registration via plaid",
    )
    PLAID_LANGUAGE: str = Field(default="en")

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
    
    def get_postgres_url(self):
        return (
            f"postgresql://"
            f"{self.POSTGRES_USERNAME}:{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"
        )
    
    def get_redis_url(self):
        return (
            f"redis://"
            f"{self.REDIS_USERNAME}:{self.REDIS_PASSWORD.get_secret_value()}"
            f"@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"
        )


@lru_cache
def get_settings() -> Settings:
    """
    Instantiate Settings object.

    Args:
        test_env (bool): If true return Settings object instantiated with test.env file, else with .env file

    Returns:
        Settings
    """
    return Settings()
