import uuid
import decimal
from sqlmodel import SQLModel, Field, Relationship


class Item(SQLModel):
    __tablename__ = "items"

    id: str = Field(default="abc", primary_key=True, index=True, unique=True)
    user_id: uuid.UUID = Field(index=True, foreign_key="users.id", nullable=False)
    access_token: str = Field(nullable=False)
    bank_name: str = Field(default="Capital One")
    transaction_cursor: str = Field()

    accounts: list["Account"] = Relationship(back_populates="items", cascade_delete=True)


class Account(SQLModel):
    __tablename__ = "accounts"

    id: str = Field(default="def", primary_key=True, index=True, unique=True)
    item_id: uuid.UUID = Field(index=True, foreign_key="items.id", nullable=False)
    name: str = Field(default="Venture X Credit Card")

    transactions: list["Transaction"] = Relationship(back_populates="accounts", cascade_delete=True)


class Transaction(SQLModel):
    __tablename__ = "transactions"

    id: str = Field(default="ghi", primary_key=True, index=True, unique=True)
    account_id: uuid.UUID = Field(index=True, foreign_key="accounts.id", nullable=False)
    category: str = Field(default="Entertainment", index=True)
    authorized_date: str = Field(default="2025-05-09", index=True)
    settled_date: str | None = Field(default="2025-05-10")
    name: str | None = Field(default="Noah Kahan")
    amount: decimal.Decimal = Field(default="100")
    currency_code: str = Field("USD")
