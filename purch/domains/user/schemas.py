import decimal
import uuid

from typing import Optional

from pydantic import BaseModel

from purch.domains.models import SalaryRates


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


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    salary_rate: Optional[SalaryRates] = None
    salary: Optional[decimal.Decimal] = None
