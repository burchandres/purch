from purch.domains.finance.service import FinanceService
from purch.domains.user.repository import UserRepository


def get_finance_service():
    return FinanceService()


def get_user_repository():
    return UserRepository()
