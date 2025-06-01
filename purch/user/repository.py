import uuid

from sqlmodel import (
    Session,
    select,
)

from purch.core.models import User
from purch.core.repository import AbstractRepository


class UserRepository(AbstractRepository):
    def add(self, user: User):
        with Session(self.engine) as session:
            session.add(user)
            session.commit()

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
