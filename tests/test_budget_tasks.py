import json
import requests
import pytest

from fastapi import status
from purch.infrastructure.plaid.tokens import get_plaid_access_token
from purch.infrastructure.taskiq.tasks import sync_transactions

BASE_BUDGET_URL = "/budget"
LINK_TOKEN_URL = BASE_BUDGET_URL + "/plaid/link-token"
SANDBOX_CREATE_PUBLIC_TOKEN_URL = "https://sandbox.plaid.com/sandbox/public_token/create"
# bank ids for testing: https://plaid.com/docs/sandbox/institutions/
FIRST_PLATYPUS_BANK_ID = "ins_109508"

@pytest.mark.anyio
async def test_sync_transactions(
    configure_test_settings,
    configure_get_current_active_user,
    test_client
):
    # get access-token for getting transactions from /transactions/sync
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
    assert public_token_response.status_code == status.HTTP_200_OK
    public_token_response_json = public_token_response.json()
    assert "public_token" in public_token_response_json
    assert "request_id" in public_token_response_json
    # hit endpoint for exchanging public -> access
    access_token_response = get_plaid_access_token(
        public_token=public_token_response_json["public_token"]
    )
    # hit transactions endpoint
    sync_transactions_task = await sync_transactions.kiq(
        access_token_response["access_token"], 
        initial_cursor=''
    )
    sync_transactions_result = await sync_transactions_task.wait_result()
    transactions, _ = sync_transactions_result.return_value
    assert "added" in transactions
    assert "modified" in transactions
    assert "removed" in transactions
    # TODO: test pulling with other cursor values