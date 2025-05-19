import uuid

from typing import Annotated
from fastapi import APIRouter, Response, Depends, HTTPException, status

from pirch.user.repository import UserRepository
from pirch.user.model import User, UserRoles
from pirch.auth.security import oauth2_scheme, get_current_active_user

router = APIRouter()


@router.get("/current", response_model=User)
def get_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@router.delete("/delete", dependencies=[Depends(oauth2_scheme)])
def delete_user(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    if (
        current_user.id != id
        or current_user.role != UserRoles.admin
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to delete this user",
        )
    user_repo = UserRepository()
    user_repo.delete_user(id=id)
    return Response(status_code=200)
