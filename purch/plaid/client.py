import plaid

from plaid.api import plaid_api
from purch.common.config import get_settings

settings = get_settings()

configuration = plaid.Configuration(
    host=settings.get_plaid_host(),
    api_key={
        "clientId": settings.PLAID_CLIENT_ID,
        "secret": settings.PLAID_SECRET.get_secret_value(),
    },
)

api_client = plaid.ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)
