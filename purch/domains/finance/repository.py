from typing import Iterable
from enum import StrEnum, auto

from sqlmodel import Session, select, delete

from purch.common.repository import AbstractPostgresRepository
from purch.domains.models import Item, Account, Transaction


class FinanceObjectTypes(StrEnum):
    item = auto()
    account = auto()
    transaction = auto()


class FinanceRepository(AbstractPostgresRepository):
    objects: dict[str, Item | Account | Transaction] = {
        FinanceObjectTypes.item.value: Item,
        FinanceObjectTypes.account.value: Account,
        FinanceObjectTypes.transaction.value: Transaction
    }
    def add(self, object: Item | Account | Transaction):
        with Session(self.engine) as session:
            session.add(object)
            session.commit()

    def add_all(self, accounts: Iterable[Item] | Iterable[Account] | Iterable[Transaction]):
        with Session(self.engine) as session:
            session.add_all(accounts)
            session.commit()

    def get(self, id: str, object_type: str) -> Item | Account | Transaction | None:
        with Session(self.engine) as session:
            object = self._get_object(object_type)
            statement = select(object).where(object.id == id)
            results = session.exec(statement)
            return results.first()

    def get_all(self, object_type: str) -> Iterable[Item] | Iterable[Account] | Iterable[Transaction]:
        with Session(self.engine) as session:
            object = self._get_object(object_type)
            statement = select(object)
            results = session.exec(statement)
            return results.all()

    def delete(self, id: str, object_type: str):
        with Session(self.engine) as session:
            object = self._get_object(object_type)
            statement = delete(object).where(object.id == id)
            session.exec(statement)
            session.commit()

    def _get_object(self, object_type: str) -> Item | Account | Transaction:
        try:
            object: Item | Account | Transaction = self.objects[object_type]
        except KeyError:
            raise ValueError("invalid object type")
        return object