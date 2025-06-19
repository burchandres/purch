from pydantic import BaseModel

from purch.domains.models import User, Item


class ItemCreate(BaseModel):
    access_token: str
    item_id: str
    user: User


class AccountsCreate(BaseModel):
    access_token: str
    item: Item
