import datetime
from typing import Optional, Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError

from purch.common.config import get_settings, Settings
from purch.domains.models import User
from purch.domains.user.repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

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


def create_purch_jwt_access_token(
    data: dict,
    settings: Settings,
    expires_delta: Optional[datetime.timedelta] = datetime.timedelta(minutes=30),
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
        to_encode,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_purch_jwt_token(token: str, settings: Settings) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Token validation failed: {str(e)}")


def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Get current user from either Authorization header or httpOnly cookie."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    token = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    else:
        token = request.cookies.get(settings.AUTH_COOKIE_NAME)

    if not token:
        raise credentials_exception

    try:
        verify_purch_jwt_token(token, settings)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_repo = UserRepository(settings=settings)
    user = user_repo.get_user_by_id(id=user_id)

    if not user:
        raise credentials_exception

    return user


@staticmethod
def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Check if user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user
