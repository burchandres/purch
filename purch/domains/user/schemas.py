import uuid

from pydantic import BaseModel

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