from pydantic import BaseModel
from typing import Optional

from purch.domains.models import User, Item, Transaction


class ItemCreate(BaseModel):
    access_token: str
    item_id: str
    user: User


class ItemUpdate(BaseModel):
    id: str
    # TODO: fill out the rest with what we could update for an item


class AccountCreate(BaseModel):
    access_token: str
    item: Item


class AccountUpdate(BaseModel):
    id: str
    # TODO: fill out the rest with what we could update for an account


class TransactionRemove(BaseModel):
    id: str
    account_id: str


class TransactionUpdate(BaseModel, Transaction):
    pending_transaction_id: str
