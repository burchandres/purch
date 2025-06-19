from sqlmodel import SQLModel, Field, Relationship

from purch.domains.item.models import Item
from purch.domains.transaction.models import Transaction


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: str = Field(default="def", primary_key=True, index=True, unique=True)
    item_id: str = Field(index=True, foreign_key="items.id", nullable=False)
    name: str = Field(default="Venture X Credit Card")

    item: Item = Relationship(back_populates="accounts")
    transactions: list["Transaction"] = Relationship(
        back_populates="account", cascade_delete=True
    )
