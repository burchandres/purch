from typing import Iterable

from sqlmodel import Session, select, delete, update

from purch.common.repository import AbstractPostgresRepository
from purch.domains.finance.schemas import (
    TransactionUpdate,
)
from purch.domains.models import Item, Account, Transaction


class ItemRepository(AbstractPostgresRepository):
    def add(self, object: Item):
        with Session(self.engine) as session:
            session.add(object)
            session.commit()

    def add_all(self, objects: Iterable[Item]):
        with Session(self.engine) as session:
            session.add_all(objects)
            session.commit()

    def get(self, id: str) -> Item | None:
        with Session(self.engine) as session:
            statement = select(Item).where(Item.id == id)
            results = session.exec(statement)
            return results.first()

    def get_all(self) -> Iterable[Item]:
        with Session(self.engine) as session:
            statement = select(Item)
            results = session.exec(statement)
            return results.all()


    def delete(self, id: str):
        with Session(self.engine) as session:
            statement = delete(Item).where(Item.id == id)
            session.exec(statement)
            session.commit()


class AccountRepository(AbstractPostgresRepository):
    def add(self, object: Account):
        with Session(self.engine) as session:
            session.add(object)
            session.commit()

    def add_all(self, objects: Iterable[Account]):
        with Session(self.engine) as session:
            session.add_all(objects)
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


class TransactionRepository(AbstractPostgresRepository):
    def add(self, object: Transaction):
        with Session(self.engine) as session:
            session.add(object)
            session.commit()

    def add_all(self, objects: Iterable[Transaction]):
        with Session(self.engine) as session:
            session.add_all(objects)
            session.commit()

    def get(self, id: str) -> Transaction | None:
        with Session(self.engine) as session:
            statement = select(Transaction).where(Transaction.id == id)
            results = session.exec(statement)
            return results.first()

    def get_all(self) -> Iterable[Transaction]:
        with Session(self.engine) as session:
            statement = select(Transaction)
            results = session.exec(statement)
            return results.all()

    def update(self, transaction_data: TransactionUpdate):
        with Session(self.engine) as session:
            transaction_data_dict = transaction_data.__dict__
            pending_transaction_id = transaction_data_dict.pop("pending_transaction_id")
            statement = (
                update(Transaction)
                .where(Transaction.id == pending_transaction_id)
                .values(transaction_data_dict)
            )
            session.exec(statement)
            session.commit()

    def delete(self, id: str):
        with Session(self.engine) as session:
            statement = delete(Transaction).where(Transaction.id == id)
            session.exec(statement)
            session.commit()
