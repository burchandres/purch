import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError

from pirch.utils.config import get_settings
from pirch.user.model import User
from pirch.user.repository import UserRepository


settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    # Argon2 parameters
    argon2__time_cost=3,
    argon2__memory_cost=2**16,
    argon2__parallelism=4,
    # Bcrypt parameters
    bcrypt__rounds=12,
)


def hash_password(password: str) -> str:
    """
    Hashes password according to encryption setting chosen.

    Args:
        password (str): The password to be hashed for storage.

    Returns:
        str: The hashed version of the password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Determines if the plain and hashed password inputs are equivalent.

    Args:
        plain_password (str): The plain text password set by user.
        hashed_password (str): A hashed password stored in the database.

    Returns:
        True if equal, otherwise false.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


def create_pirch_jwt_access_token(
    data: dict, expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()

    # Set expiration
    now = datetime.datetime.now(datetime.timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(
            minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})

    # Create JWT token
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY.get_secret_value(), algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Decode JWT token and return current user."""
    user_repo = UserRepository()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Get user from database
    user = user_repo.get_user_via_id(id=user_id)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Check if user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user
