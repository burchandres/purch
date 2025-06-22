import uuid
import plaid

from taskiq import TaskiqResultTimeoutError
from typing import Annotated
from fastapi import APIRouter, Response, Depends, HTTPException, status

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from purch.domains.user.service import UserService
from purch.domains.user.schemas import UserCreate, UserResponse, UserUpdate, UserDelete
from purch.common.config import get_settings, Settings
from purch.common.dependencies import get_user_service
from purch.domains.models import User
from purch.infrastructure.auth.schemas import Token
from purch.infrastructure.auth.service import oauth2_scheme, AuthService
from purch.infrastructure.plaid.tokens import (
    get_plaid_access_token,
    get_plaid_link_token,
)
from purch.infrastructure.plaid.schemas import LinkTokenResponse
from purch.infrastructure.taskiq.pipelines import item_account_storage_pipeline


router = APIRouter()


@router.get("/current", response_model=User)
async def get_current_user(
    current_user: Annotated[User, Depends(AuthService.get_current_active_user)],
):
    return current_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Token:
    """
    Login for access token.
    """
    token: Token = user_service.get_purch_jwt_access_token(form_data)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@router.post("/register", response_model=UserResponse)
async def register_user(
    user: UserCreate, user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponse:
    """
    Register a new user.
    """
    user_response = user_service.register_user(user)
    return user_response


@router.post("/update", dependencies=[Depends(oauth2_scheme)])
async def update_user(
    updated_user_data: UserUpdate,
    user: Annotated[User, Depends(AuthService.get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserUpdate:
    """
    Update user information.
    """
    updated_user = user_service.update_user(id=user.id, user_data=updated_user_data)
    return updated_user


@router.get("/link-token", response_model=LinkTokenResponse)
async def get_link_token(
    user: Annotated[User, Depends(AuthService.get_current_active_user)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    Generates a link-token for plaid integration.
    """
    try:
        plaid_link_token_response = get_plaid_link_token(
            settings=settings, user_id=user.id
        )
        return plaid_link_token_response
    except plaid.ApiException as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=e.body)


@router.post("/sync-bank-accounts")
async def sync_bank_accounts(
    public_token: str,
    user: Annotated[User, Depends(AuthService.get_current_active_user)],
):
    """
    Exchanges provided plaid public token for persistent access token,
    then syncs bank accounts with user profile.
    """
    try:
        plaid_access_token = get_plaid_access_token(public_token=public_token)
        # kick off task to store the item and relevant accounts for the given user
        await item_account_storage_pipeline.kiq(
            access_token=plaid_access_token["access_token"],
            item_id=plaid_access_token["item_id"],
            user=user,
        )
        return Response(
            status_code=status.HTTP_200_OK, content="Syncing account information..."
        )

    except (TaskiqResultTimeoutError, plaid.ApiException) as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=e)


@router.delete("/delete", dependencies=[Depends(oauth2_scheme)], response_model=UserDelete)
async def delete_user(
    current_user: Annotated[User, Depends(AuthService.get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    deleted_user = user_service.delete_user(current_user)
    return Response(
        status_code=status.HTTP_200_OK,
        content=f"User {current_user.username} has been deleted.",
    )
