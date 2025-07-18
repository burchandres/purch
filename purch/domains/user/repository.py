import uuid

from sqlmodel import Session, select, update
from typing import Iterable

from purch.domains.models import User, Item, Account
from purch.common.repository import AbstractPostgresRepository


class UserRepository(AbstractPostgresRepository):
    def add_user(self, user: User):
        with Session(self.engine) as session:
            session.add(user)
            session.commit()

    def add_user_item(self, item: Item):
        with Session(self.engine) as session:
            session.add(item)
            session.commit()

    def add_user_account(self, account: Account):
        with Session(self.engine) as session:
            session.add(account)
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

    def delete_user(self, user: User):
        with Session(self.engine) as session:
            session.delete(user)
            session.commit()

    def update_user(self, updated_user: User):
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
