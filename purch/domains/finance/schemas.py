import decimal

from pydantic import BaseModel
from typing import Optional

from purch.domains.models import User, Item


class ItemCreate(BaseModel):
    access_token: str
    item_id: str
    user: User


class AccountCreate(BaseModel):
    access_token: str
    item: Item


class TransactionRemove(BaseModel):
    id: str
    account_id: str


class TransactionUpdate(BaseModel):
    id: str
    pending_transaction_id: str
    # optional fields to update
    account_id: Optional[str]
    category: Optional[str]
    authorized_date: Optional[str]
    settled_date: Optional[str]
    merchant_name: Optional[str]
    amount: Optional[decimal.Decimal]
    currency_code: Optional[str]
    pending: Optional[bool]
