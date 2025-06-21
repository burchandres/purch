import decimal

from pydantic import BaseModel
from typing import Optional


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

    def to_dict(self):
        tmp = self.__dict__
        to_return = {key: value for key, value in tmp.items() if value is not None}
        return to_return
