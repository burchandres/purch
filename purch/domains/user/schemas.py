import decimal
import uuid

from typing import Optional

from pydantic import BaseModel

from purch.domains.models import IncomeRates

class UserCreate(BaseModel):
    username: str = "anders.buch"
    password: str = "password"
    first_name: str = "Anders"
    last_name: str = "Buch"


class UserResponse(BaseModel):
    id: str | uuid.UUID
    username: str
    first_name: str
    last_name: str
    income: Optional[decimal.Decimal] = None
    income_rate: Optional[IncomeRates] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    income_rate: Optional[IncomeRates] = None
    income: Optional[decimal.Decimal] = None


class UserDelete(BaseModel):
    username: str
    first_name: str
    last_name: str
