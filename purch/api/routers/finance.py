import plaid
import json

from taskiq import TaskiqResultTimeoutError
from typing import Annotated
from fastapi import APIRouter, Depends, Response, status

from purch.domains.models import User
from purch.infrastructure.plaid.tokens import (
    get_plaid_link_token,
    get_plaid_access_token,
)
from purch.infrastructure.plaid.schemas import LinkTokenResponse

# TODO: fix this import upon figuring where to put these tasks
from purch.taskiq.tasks import create_and_add_item_and_accounts, sync_transactions
from purch.domains.auth.service import get_current_active_user
from purch.common.config import Settings, get_settings

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/plaid/link-token", response_model=LinkTokenResponse)
async def get_link_token(
    user: Annotated[User, Depends(get_current_active_user)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    try:
        plaid_link_token_response = get_plaid_link_token(
            settings=settings, user_id=user.id
        )
        return plaid_link_token_response
    except plaid.ApiException as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=e.body)


# TODO: When this endpoint is hit...
#       ...sync transactions in a background task
@router.post("/plaid/access-token")
async def exchange_for_access_token(
    public_token: str, user: Annotated[User, Depends(get_current_active_user)]
):
    try:
        plaid_access_token = get_plaid_access_token(public_token=public_token)
        # kick off task to store the item and relevant accounts
        # associated with the above access token and user
        await create_and_add_item_and_accounts.kiq(
            access_token=plaid_access_token["access_token"],
            item_id=plaid_access_token["item_id"],
            user=user,
        )
        await sync_transactions.kiq()
        return Response(
            status_code=status.HTTP_200_OK, content="Syncing information for you"
        )

    except (TaskiqResultTimeoutError, plaid.ApiException) as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=e)
