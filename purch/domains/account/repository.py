from typing import Iterable

from sqlmodel import Session, select, delete

from purch.common.repository import AbstractPostgresRepository
from purch.domains.account.models import Account


class AccountRepository(AbstractPostgresRepository):
    def add(self, account: Account):
        with Session(self.engine) as session:
            session.add(account)
            session.commit()

    def add_all(self, accounts: Iterable[Account]):
        with Session(self.engine) as session:
            session.add_all(accounts)
            session.commit()

    def get(self, id: str) -> Account | None:
        with Session(self.engine) as session:
            statement = select(Account).where(Account.id == id)
            results = session.exec(statement)
            return results.first()

    def get_all(self) -> Iterable[Account]:
        with Session(self.engine) as session:
            statement = select(Account)
            results = session.exec(statement)
            return results.all()

    def delete(self, id: str):
        with Session(self.engine) as session:
            statement = delete(Account).where(Account.id == id)
            session.exec(statement)
            session.commit()
