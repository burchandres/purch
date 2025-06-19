import uuid

from typing import Annotated
from fastapi import APIRouter, Response, Depends, HTTPException, status

from purch.api.dependencies import get_user_service
from purch.domains.user.service import UserService
from purch.domains.models import User
from purch.domains.user.schemas import UserCreate, UserResponse, UserUpdate
from purch.domains.auth.service import oauth2_scheme, get_current_active_user

router = APIRouter()


@router.get("/current", response_model=User)
async def get_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

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

@router.post("/update", dependencies=[Depends(oauth2_scheme)])
async def update_user(
    updated_user_data: UserUpdate,
    id: uuid.UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """ 
    Update user information.
    """
    updated_user = user_service.update_user(id=id, user_data=updated_user_data)
    return updated_user 

@router.delete("/delete", dependencies=[Depends(oauth2_scheme)])
async def delete_user(
    id: uuid.UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """ 
    Delete a user by their ID.
    """
    user_service.delete_user(id=id)
    # If the user is deleted successfully, return a 200 OK response
    return Response(status_code=status.HTTP_200_OK)
