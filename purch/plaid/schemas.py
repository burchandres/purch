import datetime as dt

from pydantic import BaseModel


class LinkTokenResponse(BaseModel):
    link_token: str
    expiration: dt.datetime
    request_id: str
