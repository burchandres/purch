import requests
import json

from fastapi import status
from purch.finance.tokens import get_plaid_access_token

# TODO: write tests for connecting to plaid...
#       ...getting link_token to register
#       ...getting access_token from a public_token
#       ...pulling transactions

BASE_FINANCE_URL = "/finance"
LINK_TOKEN_URL = BASE_FINANCE_URL + "/plaid/link-token"
SANDBOX_CREATE_PUBLIC_TOKEN_URL = "https://sandbox.plaid.com/sandbox/public_token/create"
# bank ids for testing: https://plaid.com/docs/sandbox/institutions/
FIRST_PLATYPUS_BANK_ID = "ins_109508"


def test_get_link_token(
    test_client,
    configure_get_current_active_user
):
    link_token_response = test_client.get(
        LINK_TOKEN_URL
    )
    assert link_token_response.status_code == status.HTTP_200_OK
    response_json = link_token_response.json()
    assert "link_token" in response_json
    assert "expiration" in response_json
    assert "request_id" in response_json


def test_exchange_public_token_for_access_token(
    configure_test_settings,
    test_client
):
    test_settings = configure_test_settings
    headers = {"Content-type": "application/json"}
    public_token_response = requests.post(
        url=SANDBOX_CREATE_PUBLIC_TOKEN_URL,
        headers=headers,
        data=json.dumps(
                {
                    "client_id": test_settings.PLAID_CLIENT_ID,
                    "secret": test_settings.PLAID_SECRET.get_secret_value(),
                    "institution_id": FIRST_PLATYPUS_BANK_ID,
                    "initial_products": ["auth", "transactions"],
                }
            )
        )
    public_token_response_json = public_token_response.json()
    assert "public_token" in public_token_response_json
    assert "request_id" in public_token_response_json
    # hit endpoint for exchanging public -> access
    access_token_response = get_plaid_access_token(
        public_token=public_token_response_json["public_token"]
    )
    assert "access_token" in access_token_response
    assert "item_id" in access_token_response
    assert "request_id" in access_token_response
    