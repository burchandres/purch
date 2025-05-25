from typing import Annotated
from fastapi import APIRouter, Depends

from pirch.user.model import User
from pirch.financial.service import (
    create_plaid_link_token,
    get_plaid_access_token,
)
from pirch.auth.security import get_current_active_user

router = APIRouter()


@router.get("/link-token", response_model=str)
def create_link_token(user: Annotated[User, Depends(get_current_active_user)]):
    plaid_link_token = create_plaid_link_token(user_id=user.id)
    return plaid_link_token


@router.post("/access-token", response_model=str)
def get_access_token(public_token: str):
    plaid_access_token = get_plaid_access_token(public_token=public_token)
    return plaid_access_token
