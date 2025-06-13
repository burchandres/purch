from sqlmodel import Session

from purch.core.models import Item, Account, Transaction
from purch.core.repository import AbstractPostgresRepository


class FinanceRepository(AbstractPostgresRepository):
    def add(self, object: Item | Account | Transaction):
        with Session(self.engine) as session:
            session.add(object)
            session.commit()

    # TODO: handle updating an object: Item | Account | Transaction

    def delete(self, item: Item | Account | Transaction):
        with Session(self.engine) as session:
            session.delete(item)
            session.commit()
