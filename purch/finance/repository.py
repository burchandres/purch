from sqlmodel import Session

from purch.core.models import Item, Account, Transaction
from purch.core.repository import AbstractRepository


class ItemRepository(AbstractRepository):
    pass


class AccountRepository(AbstractRepository):
    pass


class TransactionRepository(AbstractRepository):
    pass
