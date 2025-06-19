import uuid

from sqlmodel import SQLModel, Field, Relationship

from purch.domains.user.models import User
from purch.domains.account.models import Account


class Item(SQLModel, table=True):
    __tablename__ = "items"

    id: str = Field(default="abc", primary_key=True, index=True, unique=True)
    user_id: uuid.UUID = Field(index=True, foreign_key="users.id", nullable=False)
    access_token: str = Field(nullable=False)
    bank_name: str = Field(default="Capital One", nullable=False)
    transaction_cursor: str | None = Field(default="")

    user: User = Relationship(back_populates="items")
    accounts: list["Account"] = Relationship(back_populates="item", cascade_delete=True)
