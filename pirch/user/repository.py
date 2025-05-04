import uuid

from sqlmodel import (
    SQLModel,
    create_engine,
    Session,
    select,
)

from pirch.user.model import User
from pirch.utils.config import get_settings


settings = get_settings()


class UserRepository:
    db_type_default = "postgresql"

    def __init__(self):
        engine_url = f"{self.db_type_default}://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        self.engine = create_engine(engine_url, echo=True)
        SQLModel.metadata.create_all(self.engine)  # checkfirst=True by default

    def add_user(self, user: User):
        with Session(self.engine) as session:
            session.add(user)
            session.commit()

    def get_user_via_id(self, id: uuid.UUID) -> User:
        with Session(self.engine) as session:
            statement = select(User).where(User.id == id)
            results = session.exec(statement)
            return results.first()

    def get_user_via_username(self, username: str) -> User:
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            results = session.exec(statement)
            return results.first()

    def delete_user(self, id: uuid.UUID):
        with Session(self.engine) as session:
            statement = select(User).where(User.id == id)
            user = session.exec(statement).one()
            session.delete(user)
            session.commit()
