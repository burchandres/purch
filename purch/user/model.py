import uuid
import datetime as dt

from enum import StrEnum, auto
from sqlmodel import SQLModel, Field, JSON, Column, ARRAY, String
from decimal import Decimal


class SalaryRates(StrEnum):
    hourly = auto()
    weekly = auto()
    biweekly = auto()
    bimonthly = auto()
    monthly = auto()
    annual = auto()


class User(SQLModel, table=True):
    id: uuid.UUID | None = Field(default=None, primary_key=True, unique=True)
    last_updated: float = Field(
        default=dt.datetime.timestamp(dt.datetime.now(tz=dt.timezone.utc))
    )
    first_name: str = Field(default="Anders")
    last_name: str = Field(default="Buch")
    username: str = Field(default="anders.buch", index=True, unique=True)
    password: str = Field(default="password")
    is_active: bool = Field(default=True)
    plaid_access_tokens: list[str] = Field(
        default=None, sa_column=Column(ARRAY(String))
    )
    salary: Decimal = Field(default=3958.33)
    salary_rate: SalaryRates = Field(default=SalaryRates.bimonthly)
    category_budgets: dict = Field(default_factory=dict, sa_column=Column(JSON))
