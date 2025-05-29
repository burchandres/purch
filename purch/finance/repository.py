from sqlmodel import Session

from purch.finance.models import Item, Account, Transaction
from purch.utils.repository import AbstractRepository


class ItemRepository(AbstractRepository):
    def add(self, item: Item):
        with Session(self.engine) as session:
            session.add(item)
            session.commit()

    # TODO: to delete an item we need to delete all associated accounts (which in turn involves deleting all subassociated transactions)
    def delete(self, item: Item):
        with Session(self.engine) as session:
            session.delete(item)
            session.commit()


class AccountRepository(AbstractRepository):
    def add(self, account: Account):
        with Session(self.engine) as session:
            session.add(account)
            session.commit()

    # TODO: to delete an account we also need to delete all associated transactions
    def delete(self, account: Account):
        with Session(self.engine) as session:
            session.delete(account)
            session.commit()


class TransactionRepository(AbstractRepository):
    def add(self, transaction: Transaction):
        with Session(self.engine) as session:
            session.add(transaction)
            session.commit()

    # easy to delete a single transaction
    def delete(self, transaction: Transaction):
        with Session(self.engine) as session:
            session.delete(transaction)
            session.commit()
