from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from purch.utils.config import get_settings, Settings
from purch.auth.response_models import Token
from purch.auth.security import (
    create_purch_jwt_access_token,
    verify_password,
    hash_password,
)
from purch.user.repository import UserRepository
from purch.core.models import User

router = APIRouter()


def get_user_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserRepository:
    return UserRepository(settings=settings)


# TODO: see what else we have to do to make this a completely async call
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Annotated[Settings, Depends(get_settings)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> Token:
    """
    Login for access token.
    """
    user: User = user_repo.get_via_username(username=form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_purch_jwt_access_token(
        data={"sub": str(user.id)},
        settings=settings,
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


# TODO: see what else we have to do to make this a completely async call
@router.post("/register", response_model=User)
async def register_user(
    user: User,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
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
    user.password = hash_password(user.password)
    user_repo.add(user)
    return user
