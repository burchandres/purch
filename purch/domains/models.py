import uuid
import datetime as dt
import decimal

from enum import StrEnum, auto
from sqlmodel import SQLModel, Field, Relationship


class SalaryRates(StrEnum):
    hourly = auto()
    weekly = auto()
    biweekly = auto()
    bimonthly = auto()
    monthly = auto()
    annual = auto()


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4, primary_key=True, unique=True
    )
    last_updated: float | None = Field(
        default_factory=dt.datetime.now(dt.timezone.utc).timestamp
    )
    first_name: str = Field(default="Anders")
    last_name: str = Field(default="Buch")
    username: str = Field(default="anders.buch", index=True, unique=True)
    password: str = Field(default="password")
    is_active: bool = Field(default=True)
    salary: decimal.Decimal = Field(default=decimal.Decimal(3958.33))
    salary_rate: SalaryRates = Field(default=SalaryRates.bimonthly)

    items: list["Item"] = Relationship(back_populates="user", cascade_delete=True)
    categories: list["Category"] = Relationship(
        back_populates="user", cascade_delete=True
    )


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4, primary_key=True, unique=True
    )
    user_id: uuid.UUID = Field(index=True, foreign_key="users.id", nullable=False)
    label: str = Field(default="Groceries")
    current_spending: decimal.Decimal = Field(default=0)
    budget: decimal.Decimal = Field(default=350)

    user: User = Relationship(back_populates="categories")


class Item(SQLModel, table=True):
    __tablename__ = "items"

    id: str = Field(default="abc", primary_key=True, index=True, unique=True)
    user_id: uuid.UUID = Field(index=True, foreign_key="users.id", nullable=False)
    access_token: str = Field(nullable=False)
    bank_name: str = Field(default="Capital One", nullable=False)
    transaction_cursor: str | None = Field(default="")

    user: User = Relationship(back_populates="items")
    accounts: list["Account"] = Relationship(back_populates="item", cascade_delete=True)


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: str = Field(default="def", primary_key=True, index=True, unique=True)
    item_id: str = Field(index=True, foreign_key="items.id", nullable=False)
    name: str = Field(default="Venture X Credit Card")

    item: Item = Relationship(back_populates="accounts")
    transactions: list["Transaction"] = Relationship(
        back_populates="account", cascade_delete=True
    )


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: str = Field(default="ghi", primary_key=True, index=True, unique=True)
    account_id: str = Field(index=True, foreign_key="accounts.id", nullable=False)
    category: str = Field(default="Entertainment", index=True)
    authorized_date: str = Field(default="2025-05-09", index=True)
    settled_date: str | None = Field()
    merchant_name: str | None = Field(default="Noah Kahan")
    amount: decimal.Decimal = Field(default="100")
    currency_code: str = Field("USD")
    pending: bool = Field(default=False)

    account: Account = Relationship(back_populates="transactions")
