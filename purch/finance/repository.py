from sqlmodel import Session

from purch.core.models import Item, Account, Transaction
from purch.utils.repository import AbstractRepository


class ItemRepository(AbstractRepository):
    def add(self, item: Item):
        with Session(self.engine) as session:
            session.add(item)
            session.commit()

    def delete(self, item: Item):
        with Session(self.engine) as session:
            session.delete(item)
            session.commit()


class AccountRepository(AbstractRepository):
    def add(self, account: Account):
        with Session(self.engine) as session:
            session.add(account)
            session.commit()

    def delete(self, account: Account):
        with Session(self.engine) as session:
            session.delete(account)
            session.commit()


class TransactionRepository(AbstractRepository):
    def add(self, transaction: Transaction):
        with Session(self.engine) as session:
            session.add(transaction)
            session.commit()

    def delete(self, transaction: Transaction):
        with Session(self.engine) as session:
            session.delete(transaction)
            session.commit()
