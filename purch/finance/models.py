import uuid
import decimal
from sqlmodel import SQLModel, Field


class Item(SQLModel):
    __tablename__ = "items"

    id: str = Field(default="abc", primary_key=True, index=True, unique=True)
    user_id: uuid.UUID = Field(index=True, foreign_key="users.id", nullable=False)
    access_token: str = Field(nullable=False)
    bank_name: str = Field(default="Capital One")
    transaction_cursor: str = Field()


class Account(SQLModel):
    __tablename__ = "accounts"

    id: str = Field(default="def", primary_key=True, index=True, unique=True)
    item_id: uuid.UUID = Field(index=True, foreign_key="items.id", nullable=False)
    name: str = Field(default="Venture X Credit Card")


class Transaction(SQLModel):
    __tablename__ = "transactions"

    id: str = Field(default="ghi", primary_key=True, index=True, unique=True)
    account_id: uuid.UUID = Field(index=True, foreign_key="accounts.id", nullable=False)
    user_id: uuid.UUID = Field(index=True, foreign_key="users.id", nullable=False)
    category: str = Field(default="Entertainment")
    authorized_date: str = Field(default="2025-05-09")
    settled_date: str = Field(default="2025-05-10")
    name: str = Field(default="Noah Kahan")
    amount: decimal.Decimal = Field(default="100")
    currency_code: str = Field("USD")
    is_removed: bool = Field(default=False)
