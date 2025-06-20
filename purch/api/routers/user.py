import uuid

from typing import Annotated
from fastapi import APIRouter, Response, Depends, HTTPException, status

from purch.common.dependencies import get_user_repository
from purch.domains.models import User
from purch.domains.user.repository import UserRepository
from purch.infrastructure.auth.service import oauth2_scheme, get_current_active_user

router = APIRouter()


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
