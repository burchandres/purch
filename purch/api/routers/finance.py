import plaid
import time

from taskiq import TaskiqResultTimeoutError
from typing import Annotated
from fastapi import APIRouter, Depends, Response, status

from purch.domains.models import User
from purch.infrastructure.plaid.tokens import (
    get_plaid_link_token,
    get_plaid_access_token,
)
from purch.infrastructure.plaid.schemas import LinkTokenResponse

from purch.infrastructure.taskiq.tasks import (
    create_and_add_item_and_accounts,
    sync_transactions,
)
from purch.infrastructure.auth.service import get_current_active_user
from purch.common.config import Settings, get_settings

router = APIRouter()


@router.get("/plaid/link-token", response_model=LinkTokenResponse)
async def get_link_token(
    user: Annotated[User, Depends(get_current_active_user)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    Generates a link-token for plaid integration.

    Args:
        user (User): Currently logged in user injected into endpoint
        settings (Settings): Application settings injected into endpoint

    Returns:
        LinkTokenResponse: plaid link token and other metadata
    """
    try:
        plaid_link_token_response = get_plaid_link_token(
            settings=settings, user_id=user.id
        )
        return plaid_link_token_response
    except plaid.ApiException as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=e.body)


@router.post("/plaid/access-token")
async def exchange_for_access_token(
    public_token: str, user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Exchanges the provided plaid public token for a persistent access token for future communication with plaid.

    Args:
        public_token (str): The plaid public token generated upon successful registration
        user (User): FastAPI injected user that is currently logged in

    Returns:
        None.
    """
    try:
        plaid_access_token = get_plaid_access_token(public_token=public_token)
        # kick off task to store the item and relevant accounts for the given user
        await create_and_add_item_and_accounts.kiq(
            access_token=plaid_access_token["access_token"],
            item_id=plaid_access_token["item_id"],
            user=user,
        )
        return Response(
            status_code=status.HTTP_200_OK, content="Syncing information for you"
        )

    except (TaskiqResultTimeoutError, plaid.ApiException) as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=e)


@router.get("/sync-transactions")
async def manually_sync_transactions(
    user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Manual way of syncing transactions if requested by user.

    Args:
        user (User): Currently logged in user injected into endpoint

    Returns:
        None. Updates postgres and sends webhook notification to UI if transactions were added/modified.
    """
    await sync_transactions.kiq(user=user)
    return Response(status_code=status.HTTP_200_OK, content="Syncing transactions...")
