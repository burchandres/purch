import uuid

from enum import StrEnum, auto

from purch.domains.models import User
from purch.domains.auth.service import hash_password
from purch.domains.user.repository import UserRepository
from purch.domains.user.schemas import UserCreate, UserResponse, UserUpdate


class BaseCategories(StrEnum):
    """
    Base categories for the application.
    """

    groceries = auto()
    entertainment = auto()
    miscellaneous = auto()
    rent = auto()
    dining = auto()


class UserService:
    def __init__(self):
        self.user_repo = UserRepository()
        pass

    def register_user(self, user_data: UserCreate) -> UserResponse:
        """
        Register a new user with the provided user data.
        """
        existing_user = self.user_repo.get_via_username(username=user_data.username)

        # If user already exists, return None
        if existing_user is not None:
            return None

        # If user does not exist, add the user to the repository and return the newly created user response
        user_data.password = hash_password(user_data.password)
        user_to_register = User(
            username=user_data.username,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        self.user_repo.add(user_to_register)
        newly_created_user = self.user_repo.get_via_username(
            username=user_data.username
        )
        return UserResponse(
            id=newly_created_user.id,
            username=newly_created_user.username,
            first_name=newly_created_user.first_name,
            last_name=newly_created_user.last_name,
        )

    def update_user(self, id: str | uuid.UUID, user_data: UserUpdate) -> UserResponse:
        """
        Update user information.
        """
        existing_user = self.user_repo.get(id=id)

        # If user does not exist, raise an exception
        if existing_user is None:
            raise ValueError("User not found")

        # Update the user data
        if user_data.first_name is not None:
            existing_user.first_name = user_data.first_name
        if user_data.last_name is not None:
            existing_user.last_name = user_data.last_name
        if user_data.username is not None:
            existing_user.username = user_data.username
        if user_data.password is not None:
            existing_user.password = hash_password(user_data.password)
        if user_data.salary_rate is not None:
            existing_user.salary_rate = user_data.salary_rate
        if user_data.salary is not None:
            existing_user.salary = user_data.salary

        # Save the updated user back to the repository
        self.user_repo.update(existing_user)

        return UserResponse(
            id=existing_user.id,
            username=existing_user.username,
            first_name=existing_user.first_name,
            last_name=existing_user.last_name,
        )

    def delete_user(self, id: str | uuid.UUID) -> None:
        """
        Delete a user by their ID.
        """
        self.user_repo.delete(id=id)
