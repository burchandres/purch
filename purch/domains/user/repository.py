import uuid

from sqlmodel import Session, select, update
from typing import Iterable

from purch.domains.models import User
from purch.common.repository import AbstractPostgresRepository


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
            return results.all()

    def get(self, id: uuid.UUID) -> User:
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

    def update(self, updated_user: User):
        with Session(self.engine) as session:
            statement = (
                update(User)
                .where(User.id == updated_user.id)
                .values(
                    first_name=updated_user.first_name,
                    last_name=updated_user.last_name,
                    username=updated_user.username,
                    password=updated_user.password,
                    salary_rate=updated_user.salary_rate,
                    salary=updated_user.salary,
                )
            )
            session.exec(statement)
            session.commit()
