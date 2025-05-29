from typing import Annotated
from fastapi import APIRouter, Depends, Response, status

from purch.user.models import User
from purch.finance.tokens import get_plaid_link_token, get_plaid_access_token
from purch.auth.security import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/link-token")
def get_link_token(user: Annotated[User, Depends(get_current_active_user)]):
    plaid_link_token = get_plaid_link_token(user_id=user.id)
    return Response(status_code=status.HTTP_200_OK, content=plaid_link_token)


@router.post("/access-token")
def get_access_token(public_token: str):
    plaid_access_token = get_plaid_access_token(public_token=public_token)
    return Response(status_code=status.HTTP_200_OK, conten=plaid_access_token)


@router.get("/transactions")
def get_transactions(user: Annotated[User, Depends(get_current_active_user)]):
    pass
