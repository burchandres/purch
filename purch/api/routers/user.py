import uuid

from typing import Annotated
from fastapi import APIRouter, Response, Depends, HTTPException, status

from purch.domains.user.service import UserService
from purch.domains.models import User
from purch.domains.user.schemas import UserCreate, UserResponse
from purch.domains.auth.service import hash_password, oauth2_scheme, get_current_active_user

router = APIRouter()


def get_user_service() -> UserService:
    return UserService()


@router.get("/current", response_model=User)
async def get_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@router.delete("/delete", dependencies=[Depends(oauth2_scheme)])
async def delete_user(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
):
    if current_user.id != id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You can only delete your own account",
        )
    user_repo.delete(id=id)
    return Response(status_code=200)


@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """
    Register a new user.
    """
    new_user = user_service.register_user(user_data=user_data)
    # If user already exists return bad request
    if new_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with given username is already registered",
        )
    # If not, return the newly created user
    return new_user