from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from pirch.utils.config import get_settings
from pirch.auth.schemas import Token
from pirch.auth.security import (
    create_access_token,
    verify_password,
    hash_password,
)
from pirch.user.engine import UserDB
from pirch.user.model import User


settings = get_settings()

router = APIRouter()


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    Login for access token.
    """
    db = UserDB()
    user: User = db.get_user_via_username(username=form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=User)
def register_user(
    user: User,
) -> User:
    """
    Register a new user.
    """
    db = UserDB()
    existing_user = db.get_user_via_username(username=user.username)
    # If user already exists return bad request
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with given username already registered",
        )
    # If not, add user to user db
    user.password = hash_password(user.password)
    db.add_user(user)
    return user
