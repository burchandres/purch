import pytest

from fastapi import status

# TODO: write tests for connecting to plaid...
#       ...getting link_token to register
#       ...getting public_token after registering
#       ...getting persistent access_token for an item
#       ...pulling transactions

BASE_FINANCE_URL = "/plaid"
LINK_TOKEN_URL = BASE_FINANCE_URL + "/link-token"


def test_get_link_token(
        configure_test_settings, 
        configure_get_active_user, 
        test_db_name, 
        test_client
    ):
    link_token_response = test_client.get(
        LINK_TOKEN_URL
    )
    assert link_token_response.status_code == status.HTTP_200_OK
    # link_token_dict = link_token_response.json()
    
