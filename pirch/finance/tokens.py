import plaid
import json
from plaid.model.products import Products
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_create_request_statements import (
    LinkTokenCreateRequestStatements,
)
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from uuid import UUID
from datetime import date, timedelta

from pirch.finance.plaid import client
from pirch.utils.config import get_settings


settings = get_settings()


def create_plaid_link_token(user_id: UUID):
    """
    This generates a link token which allows the user to connect to Plaid via Link.

    Args:
        user_id (UUID): User.id field value -- i.e. UUID generated upon user registration with Pirch

    Returns:
        str: The link token required to allow the user to register with Plaid via Link.
    """
    try:
        request = LinkTokenCreateRequest(
            products=settings.get_plaid_products(),
            client_name=settings.PRODUCT_NAME,
            country_codes=settings.get_plaid_country_codes(),
            language=settings.PLAID_LANGUAGE,
            user=LinkTokenCreateRequestUser(client_user_id=str(user_id)),
        )
        if settings.PLAID_REDIRECT_URI != None:
            request["redirect_uri"] = settings.PLAID_REDIRECT_URI
        if Products("statements") in settings.get_plaid_products():
            statements = LinkTokenCreateRequestStatements(
                end_date=date.today(), start_date=date.today() - timedelta(days=30)
            )
            request["statements"] = statements
        # create link token
        response = client.link_token_create(request)
        return response
    except plaid.ApiException as e:
        return json.loads(e.body)


# TODO: make onSuccess function in frontend to feed to this endpoint
def get_plaid_access_token(public_token: str):
    """
    Exchanges the generated public token by Link upon successful registration for a persistent access token.

    Args:
        public_token (str): The public token provided by link for a user.

    Returns:
        str: Returns the access token which will be persisted under User.plaid_access_token to communicate with plaid in the future.
    """
    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        return exchange_response
    except plaid.ApiException as e:
        return json.loads(e.body)
