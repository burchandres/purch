import decimal

from sqlmodel import SQLModel, Field, Relationship

from purch.domains.account.models import Account


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: str = Field(default="ghi", primary_key=True, index=True, unique=True)
    account_id: str = Field(index=True, foreign_key="accounts.id", nullable=False)
    category: str = Field(default="Entertainment", index=True)
    authorized_date: str = Field(default="2025-05-09", index=True)
    settled_date: str | None = Field(default="2025-05-10")
    name: str | None = Field(default="Noah Kahan")
    amount: decimal.Decimal = Field(default="100")
    currency_code: str = Field("USD")

    account: Account = Relationship(back_populates="transactions")