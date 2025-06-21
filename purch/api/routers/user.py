import uuid
import plaid

from taskiq import TaskiqResultTimeoutError
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Response, Depends, HTTPException, status

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from purch.common.config import get_settings, Settings
from purch.common.dependencies import get_user_repository, get_auth_service
from purch.domains.models import User
from purch.domains.user.repository import UserRepository
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
    settings: Annotated[Settings, Depends(get_settings)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """
    Login for access token.
    """
    user: User = user_repo.get_via_username(username=form_data.username)
    if not user or not auth_service.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_purch_jwt_access_token(
        data={"sub": str(user.id)},
        settings=settings,
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=User)
async def register_user(
    user: User,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> User:
    """
    Register a new user.
    """
    existing_user = user_repo.get_via_username(username=user.username)
    # If user already exists return bad request
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with given username is already registered",
        )
    # If not, add user to user repo
    user.password = auth_service.hash_password(user.password)
    user_repo.add(user)
    return user


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


@router.post("/pull-bank-accounts")
async def pull_bank_accounts(
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


@router.delete("/delete", dependencies=[Depends(oauth2_scheme)])
async def delete_user(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(AuthService.get_current_active_user)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    if current_user.id != id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You can only delete your own account",
        )
    user_repo.delete(id=id)
    return Response(status_code=200)
