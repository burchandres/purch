from sqlmodel import Session

from purch.common.repository import AbstractPostgresRepository
from purch.domains.models import Transaction

class BudgetRepository(AbstractPostgresRepository):
    def add_new_transactions(self, transactions: list[Transaction]):
        with Session(self.engine) as session:
            session.add_all(transactions)
            session.commit()
