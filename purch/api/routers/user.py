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
from purch.infrastructure.auth.service import get_current_active_user
from purch.infrastructure.plaid.tokens import (
    get_plaid_access_token,
    get_plaid_link_token,
)
from purch.infrastructure.plaid.schemas import LinkTokenResponse
from purch.infrastructure.taskiq.pipelines import item_account_storage_pipeline


router = APIRouter()


@router.get("/current", response_model=User)
async def get_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@router.post("/token", response_model=Response)
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Response:
    """
    Login for access token.
    """
    try:
        token: Token = user_service.get_purch_jwt_access_token(form_data)
    except ValueError as e:
        return Response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=user_service.settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES,
        path="/",
    )

    return Response(
        status_code=status.HTTP_200_OK, content="User logged in successfully"
    )


@router.post("/logout", response_model=Response)
def logout(response: Response) -> Response:
    response.delete_cookie("access_token", path="/")
    return Response(
        status_code=status.HTTP_200_OK, content="User logged out successfully"
    )


@router.post("/register", response_model=UserResponse)
async def register_user(
    user: UserCreate, user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponse:
    """
    Register a new user.
    """
    try:
        user_response = user_service.register_user(user)
    except ValueError as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))
    return user_response


@router.patch("/update", response_model=UserResponse)
async def update_user(
    user_update_data: UserUpdate,
    user: Annotated[User, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """
    Update user information.
    """
    try:
        updated_user = user_service.update_user(id=user.id, user_data=user_update_data)
    except ValueError as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))
    return updated_user


@router.get("/link-token", response_model=LinkTokenResponse)
async def get_link_token(
    user: Annotated[User, Depends(get_current_active_user)],
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
    user: Annotated[User, Depends(get_current_active_user)],
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


@router.delete("/delete", response_model=UserDelete)
async def delete_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    deleted_user = user_service.delete_user(current_user)
    return deleted_user
