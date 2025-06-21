from sqlmodel import Session, update, delete

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
            for transaction_to_update in transactions:
                statement = (
                    update(Transaction)
                    .where(Transaction.id == transaction_to_update.pending_transaction_id)
                    .values(transaction_to_update.to_dict())
                )
                session.exec(statement)
            session.commit()

    def delete_transactions(self, transaction_ids: list[str]):
        with Session(self.engine) as session:
            statement = delete(Transaction).where(Transaction.id in transaction_ids)
            session.exec(statement)
            session.commit()
