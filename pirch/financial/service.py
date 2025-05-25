import plaid
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_statements import (
    LinkTokenCreateRequestStatements,
)
from plaid.api import plaid_api

from pirch.utils.config import get_settings

settings = get_settings()

configuration = plaid.Configuration(
    host=settings.get_plaid_host(),
    api_key={
        "clientId": settings.PLAID_CLIENT_ID,
        "secret": settings.PLAID_SECRET.get_secret_value(),
        "plaidVersion": "2023-09-29",
    },
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)


# TODO: start here
def create_link_token():
    pass


# TODO: then here?  need to figure out link flow...
def get_access_token():
    pass
