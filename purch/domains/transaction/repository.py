from typing import Iterable

from sqlmodel import Session, select, delete

from purch.common.repository import AbstractPostgresRepository
from purch.domains.transaction.models import Transaction


class TransactionRepository(AbstractPostgresRepository):
    def add(self, transaction: Transaction):
        with Session(self.engine) as session:
            session.add(transaction)
            session.commit()

    def add_all(self, transactions: Iterable[Transaction]):
        with Session(self.engine) as session:
            session.add_all(transactions)
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

    def delete(self, id: str):
        with Session(self.engine) as session:
            statement = delete(Transaction).where(Transaction.id == id)
            session.exec(statement)
            session.commit()
