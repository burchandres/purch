import uuid

from sqlmodel import (
    Session,
    select,
)
from typing import Iterable

from purch.core.models import User
from purch.core.repository import AbstractPostgresRepository


class UserRepository(AbstractPostgresRepository):
    def add(self, user: User):
        with Session(self.engine) as session:
            session.add(user)
            session.commit()

    def add_all(self, users: Iterable[User]):
        with Session(self.engine) as session:
            session.add_all(users)
            session.commit()

    def get_all(self) -> Iterable[User]:
        with Session(self.engine) as session:
            statement = select(User)
            results = session.exec(statement)
            return results

    def get_via_id(self, id: uuid.UUID) -> User:
        with Session(self.engine) as session:
            statement = select(User).where(User.id == id)
            results = session.exec(statement)
            return results.first()

    def get_via_username(self, username: str) -> User:
        with Session(self.engine) as session:
            statement = select(User).where(User.username == username)
            results = session.exec(statement)
            return results.first()

    def delete(self, id: uuid.UUID):
        with Session(self.engine) as session:
            statement = select(User).where(User.id == id)
            user = session.exec(statement).one()
            session.delete(user)
            session.commit()
