from typing import Iterable
from enum import StrEnum, auto

from sqlmodel import Session, select

from purch.core.models import Item, Account, Transaction
from purch.core.repository import AbstractPostgresRepository


class FinanceObjects(StrEnum):
    item = auto()
    account = auto()
    transaction = auto()


class FinanceRepository(AbstractPostgresRepository):
    def add(self, object: Item | Account | Transaction):
        with Session(self.engine) as session:
            session.add(object)
            session.commit()

    def add_all(self, objects: Iterable[Item] | Iterable[Account] | Iterable[Transaction]):
        with Session(self.engine) as session:
            session.add_all(objects)
            session.commit()

    def get_all(self, object_type: FinanceObjects) -> Iterable[Item] | Iterable[Account] | Iterable[Transaction]:
        statement = None
        match object_type:
            case FinanceObjects.item:
                statement = select(Item)
            case FinanceObjects.account:
                statement = select(Account)
            case FinanceObjects.transaction:
                statement = select(Transaction)
        if statement is None:
            raise ValueError("Invalid object_type being queried. Must be one of the FinanceObjects enums.")
        with Session(self.engine) as session:
            results = session.exec(statement)
            return results
        
    # TODO: handle updating an object: Item | Account | Transaction

    def delete(self, item: Item | Account | Transaction):
        with Session(self.engine) as session:
            session.delete(item)
            session.commit()
