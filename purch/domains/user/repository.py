import uuid

from sqlmodel import (
    Session,
    select,
)
from typing import Iterable

from purch.domains.models import User
from purch.common.repository import AbstractPostgresRepository


class UserRepository(AbstractPostgresRepository):
    def add_user(self, user: User):
        with Session(self.engine) as session:
            session.add(user)
            session.commit()

    def add_all_users(self, users: Iterable[User]):
        with Session(self.engine) as session:
            session.add_all(users)
            session.commit()

    def get_all_users(self) -> Iterable[User]:
        with Session(self.engine) as session:
            statement = select(User)
            results = session.exec(statement)
            return results.all()

    def get_user_by_id(self, id: uuid.UUID) -> User:
        with Session(self.engine) as session:
            statement = select(User).where(User.id == id)
            results = session.exec(statement)
            return results.first()

    def get_user_by_username(self, username: str) -> User:
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
