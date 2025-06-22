from sqlmodel import Session, update, delete, insert

from purch.common.repository import AbstractPostgresRepository
from purch.domains.models import Transaction
from purch.domains.budget.schemas import TransactionUpdate


class BudgetRepository(AbstractPostgresRepository):
    def add_new_transactions(self, transactions: list[Transaction]):
        with Session(self.engine) as session:
            session.add_all(transactions)
            session.commit()

    def update_transactions(self, transactions: list[TransactionUpdate]):
        with Session(self.engine) as session:
            statement = update(Transaction)
            session.exec(statement, [txn.to_dict() for txn in transactions])
            session.commit()

    def delete_transactions(self, transaction_ids: list[str]):
        with Session(self.engine) as session:
            statement = delete(Transaction)
            session.exec(statement, [{"id": txn_id for txn_id in transaction_ids}])
            session.commit()
