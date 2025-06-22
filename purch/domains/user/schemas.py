import decimal
import uuid

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
    first_name: str | None
    last_name: str | None
    username: str | None
    password: str | None
    salary_rate: SalaryRates | None
    salary: decimal.Decimal | None
