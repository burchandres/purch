from typing import Annotated
from fastapi import APIRouter, Depends, Response, status

from pirch.user.model import User
from pirch.finance.tokens import (
    create_plaid_link_token,
    get_plaid_access_token,
)
from pirch.auth.security import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/link-token")
def create_link_token(user: Annotated[User, Depends(get_current_active_user)]):
    plaid_link_token = create_plaid_link_token(user_id=user.id)
    return Response(status_code=status.HTTP_200_OK, content=plaid_link_token)


@router.post("/access-token")
def get_access_token(
    public_token: str
):
    plaid_access_token = get_plaid_access_token(public_token=public_token)
    return Response(status_code=status.HTTP_200_OK, conten=plaid_access_token)
