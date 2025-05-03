import uuid
from enum import StrEnum, auto
from sqlmodel import SQLModel, Field


class UserRoles(StrEnum):
    basic = auto()
    pro = auto()
    admin = auto()

    @staticmethod
    def get_role_value(role: str) -> int:
        # Order is preserved with how enums are added
        for i, user_role in enumerate(UserRoles):
            if user_role == role:
                return i
        raise ValueError(f"Role '{role}' is not a valid user role.")
    


class User(SQLModel, table=True):
    id: uuid.UUID | None = Field(default=None, primary_key=True)
    full_name: str = Field(default="Anders Buch")
    username: str = Field(default="anders.buch", index=True, unique=True)
    password: str = Field(default="password")
    role: UserRoles = Field(default=UserRoles.admin)
    is_active: bool = Field(default=True)
