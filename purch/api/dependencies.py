from purch.domains.user.service import UserService


def get_user_service() -> UserService:
    return UserService()
