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

from purch.infrastructure.plaid.client import plaid_client
from purch.infrastructure.plaid.schemas import LinkTokenResponse
from purch.common.config import get_settings, Settings


def get_plaid_link_token(settings: Settings, user_id: UUID) -> LinkTokenResponse:
    """
    This generates a link token which allows the user to connect to Plaid via Link.

    Args:
        user_id (UUID): User.id field value -- i.e. UUID generated upon user registration with Purch

    Returns:
        str: The link token required to allow the user to register with Plaid via Link.
    """
    settings = get_settings()
    request = LinkTokenCreateRequest(
        products=settings.get_plaid_products(),
        client_name=settings.PRODUCT_NAME,
        country_codes=settings.get_plaid_country_codes(),
        language=settings.PLAID_LANGUAGE,
        user=LinkTokenCreateRequestUser(client_user_id=str(user_id)),
    )
    if settings.PLAID_REDIRECT_URI is not None:
        request["redirect_uri"] = settings.PLAID_REDIRECT_URI
    if Products("statements") in settings.get_plaid_products():
        statements = LinkTokenCreateRequestStatements(
            end_date=date.today(), start_date=date.today() - timedelta(days=30)
        )
        request["statements"] = statements
    # create link token
    response = plaid_client.link_token_create(request).to_dict()
    # TODO: streamline this with a helper function if needed
    link_token_response = LinkTokenResponse(
        link_token=response["link_token"],
        expiration=response["expiration"],
        request_id=response["request_id"],
    )
    return link_token_response


def get_plaid_access_token(public_token: str):
    """
    Exchanges the generated public token by Link upon successful registration for a persistent access token.

    Args:
        public_token (str): The public token provided by link for a user.

    Returns:
        dict: Returns the access token response object which contains the following keys:
            * access_token: will be persisted under User.plaid_access_token to communicate with plaid in the future.
            * item_id: the item_id value associated with the Item associated with the returned access_token
            * request_id: unique identifier for the request
    """
    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = plaid_client.item_public_token_exchange(
        exchange_request
    ).to_dict()
    return exchange_response