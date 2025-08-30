from typing import Annotated
from fastapi import APIRouter, Depends, Response, status

from purch.domains.models import User, Transaction
from purch.infrastructure.taskiq.tasks import (
    sync_transactions,
)
from purch.infrastructure.auth.service import get_current_active_user

router = APIRouter()


@router.get("/sync-transactions")
async def manually_sync_transactions(
    user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Manual way of syncing transactions if requested by user.
    """
    await sync_transactions.kiq(user=user)
    return Response(status_code=status.HTTP_200_OK, content="Syncing transactions...")


@router.get("/get-transactions", response_model=list[Transaction])
async def get_user_transactions(
        user: Annotated[User, Depends(get_current_active_user)],
) -> list[Transaction]:
    """
    Get all transactions for a user
    """
    transactions = [
        transaction for item in user.items for account in item.accounts for transaction in account.transactions]
    return transactions
