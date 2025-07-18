# Anything wrapped inside of a fastapi.Depends or taskiq.TaskiqDepends goes here

from purch.domains import BudgetService, UserService
from purch.domains.user.repository import UserRepository


def get_budget_service() -> BudgetService:
    return BudgetService()


def get_user_service() -> UserService:
    return UserService()


def get_user_repository() -> UserRepository:
    return UserRepository()
