from purch.domains.user.repository import UserRepository
from purch.domains.models import User


class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def refresh_user(self, user: User):
        user = self.user_repo.get(user.id)
        return user
