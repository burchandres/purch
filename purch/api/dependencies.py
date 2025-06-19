from purch.domains.finance.service import FinanceService
from purch.domains.user.service import UserService


def get_finance_service() -> FinanceService:
    return FinanceService()


def get_user_service() -> UserService:
    return UserService
