import pytest

from purch.infrastructure.taskiq.tasks import sync_transactions


SANDBOX_CREATE_PUBLIC_TOKEN_URL = "https://sandbox.plaid.com/sandbox/public_token/create"
# bank ids for testing: https://plaid.com/docs/sandbox/institutions/
FIRST_PLATYPUS_BANK_ID = "ins_109508"

@pytest.mark.anyio
async def test_sync_transactions(
    configure_test_settings,
    test_user,
):
    test_user = test_user
    # hit transactions endpoint
    # TODO: populate the database with a fake item, accounts with said item and transactions per account
    await sync_transactions.kiq(user=test_user)