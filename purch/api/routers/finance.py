import plaid
import time

from taskiq import TaskiqResultTimeoutError
from typing import Annotated
from fastapi import APIRouter, Depends, Response, status

from purch.domains.models import User
from purch.domains.user.service import UserService
from purch.infrastructure.plaid.tokens import (
    get_plaid_link_token,
    get_plaid_access_token,
)
from purch.infrastructure.plaid.schemas import LinkTokenResponse

# TODO: fix this import upon figuring where to put these tasks
from purch.infrastructure.taskiq.tasks import create_and_add_item_and_accounts, sync_transactions
from purch.infrastructure.auth.service import get_current_active_user
from purch.common.config import Settings, get_settings
from purch.api.dependencies import get_user_service

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


@router.post("/plaid/access-token")
async def exchange_for_access_token(
    public_token: str, 
    user: Annotated[User, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    try:
        plaid_access_token = get_plaid_access_token(public_token=public_token)
        # kick off task to store the item and relevant accounts
        # associated with the above access token and user
        item_accounts_task = await create_and_add_item_and_accounts.kiq(
            access_token=plaid_access_token["access_token"],
            item_id=plaid_access_token["item_id"],
            user=user,
        )
        # wait till above task finishes
        while not item_accounts_task.is_ready():
            time.sleep(0.1)
        # kick off task to sync transactions
        # TODO: setup webhook to pull whenever new transactions are available?
        await sync_transactions.kiq(user=user_service.refresh_user(user))
        return Response(
            status_code=status.HTTP_200_OK, content="Syncing information for you"
        )

    except (TaskiqResultTimeoutError, plaid.ApiException) as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=e)
