import plaid
import json

from typing import Annotated
from fastapi import APIRouter, Depends, Response, status

from purch.core.models import User
from purch.finance.tokens import get_plaid_link_token, get_plaid_access_token
from purch.finance.response_models import LinkTokenResponse
from purch.auth.security import get_current_active_user
from purch.utils.config import Settings, get_settings

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/link-token", response_model=LinkTokenResponse)
def get_link_token(
    user: Annotated[User, Depends(get_current_active_user)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    try:
        plaid_link_token_response = get_plaid_link_token(
            settings=settings, 
            user_id=user.id
        )
        return plaid_link_token_response
    except plaid.ApiException as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=e.body)


# TODO: When this endpoint is hit get access token and sync transactions in a background task
@router.post("/access-token")
def get_access_token(public_token: str):
    try:
        plaid_access_token = get_plaid_access_token(public_token=public_token)
        return Response(
            status_code=status.HTTP_200_OK, content=json.dumps(plaid_access_token)
        )
    except plaid.ApiException as e:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=e)
