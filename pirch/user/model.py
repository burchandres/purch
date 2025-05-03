import uuid
from enum import Enum
from sqlmodel import SQLModel, Field


class UserRoles(Enum):
    basic = 0
    pro = 1
    admin = 2

    @staticmethod
    def get_role_value(role: str) -> int:
        if role in UserRoles.__members__:
            return UserRoles[role].value
        else:
            raise ValueError(f"Role '{role}' is not a valid user role.")


class User(SQLModel, table=True):
    id: uuid.UUID | None = Field(default=None, primary_key=True)
    full_name: str = Field(default="Anders Buch")
    username: str = Field(default="anders.buch", index=True, unique=True)
    password: str = Field(default="password")
    role: str = Field(default="admin")
    is_active: bool = Field(default=True)
