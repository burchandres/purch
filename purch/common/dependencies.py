# Anything wrapped inside of a fastapi.Depends or taskiq.TaskiqDepends goes here

from purch.domains.finance.service import FinanceService
from purch.domains.finance.repository import (
    ItemRepository,
    AccountRepository,
    TransactionRepository,
)
from purch.domains.user.service import UserService
from purch.domains.user.repository import UserRepository


def get_finance_service() -> FinanceService:
    return FinanceService()


def get_item_repository() -> ItemRepository:
    return ItemRepository()


def get_account_repository() -> AccountRepository:
    return AccountRepository()


def get_transaction_repository() -> TransactionRepository:
    return TransactionRepository()


def get_user_service() -> UserService:
    return UserService()


def get_user_repository() -> UserRepository:
    return UserRepository()
