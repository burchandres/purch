import uuid
import datetime as dt

from enum import StrEnum, auto
from sqlmodel import SQLModel, Field, JSON, Column, Relationship
from decimal import Decimal

from purch.finance.models import Item, Transaction


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
    salary: Decimal = Field(default=3958.33)
    salary_rate: SalaryRates = Field(default=SalaryRates.bimonthly)
    category_budgets: dict = Field(default_factory=dict, sa_column=Column(JSON))

    items: list["Item"] = Relationship(back_populates="users", cascade_delete=True)
