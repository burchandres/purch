from typing import Annotated
from fastapi import APIRouter, Depends, Response, status

from purch.domains.models import User
from purch.infrastructure.taskiq.tasks import (
    sync_transactions,
)
from purch.infrastructure.auth.service import AuthService

router = APIRouter()


@router.get("/sync-transactions")
async def manually_sync_transactions(
    user: Annotated[User, Depends(AuthService.get_current_active_user)],
):
    """
    Manual way of syncing transactions if requested by user.
    """
    await sync_transactions.kiq(user=user)
    return Response(status_code=status.HTTP_200_OK, content="Syncing transactions...")
