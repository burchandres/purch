import uuid
import datetime as dt

from fastapi.security import OAuth2PasswordRequestForm
from plaid.models import AccountsGetRequest, ItemGetRequest

from purch.domains.user.repository import UserRepository
from purch.domains.user.schemas import UserCreate, UserResponse, UserUpdate, UserDelete
from purch.domains.models import User, Item, Account
from purch.common.logger import get_logger
from purch.infrastructure.plaid.client import plaid_client
from purch.common.config import get_settings, Settings
from purch.infrastructure.auth.schemas import Token
from purch.infrastructure.auth.service import (
    hash_password,
    create_purch_jwt_access_token,
    verify_password,
)

logger = get_logger(__name__)


class UserService:
    def __init__(
        self,
        user_repo: UserRepository | None = None,
        settings: Settings | None = None,
    ):
        self.settings = settings or get_settings()
        self.user_repo = user_repo or UserRepository(self.settings)

    def register_user(self, user_data: UserCreate) -> UserResponse:
        """
        Register a new user with the provided user data.
        """
        existing_user = self.user_repo.get_user_by_username(username=user_data.username)

        # If user already exists, return None
        if existing_user is not None:
            raise ValueError(
                f"User with username {user_data.username} already exists..."
            )

        # If user does not exist, add the user to the repository and return the newly created user response
        user_data.password = hash_password(user_data.password)
        user_to_register = User(
            username=user_data.username,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        self.user_repo.add_user(user_to_register)
        newly_created_user = self.user_repo.get_user_by_username(
            username=user_data.username
        )
        return UserResponse(
            id=newly_created_user.id,
            username=newly_created_user.username,
            first_name=newly_created_user.first_name,
            last_name=newly_created_user.last_name,
            salary=newly_created_user.salary,
            salary_rate=newly_created_user.salary_rate,
        )

    def get_purch_jwt_access_token(
        self, login_form_data: OAuth2PasswordRequestForm
    ) -> Token:
        """
        Generates jwt access token for client side.

        Args:
            login_form_data (dict): Dictionary containing username and password keys.

        Returns:
            (Token | None):  Token if valid user, else none.
        """
        user = self.user_repo.get_user_by_username(username=login_form_data.username)
        if user is None or not verify_password(login_form_data.password, user.password):
            raise ValueError("User with provided login credentials doesn't exist...")
        access_token_expires = dt.timedelta(
            minutes=self.settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_purch_jwt_access_token(
            data={"sub": str(user.id)},
            settings=self.settings,
            expires_delta=access_token_expires,
        )
        return Token(access_token=access_token, token_type="bearer")

    def update_user(self, id: str | uuid.UUID, user_data: UserUpdate) -> UserResponse:
        """
        Update user information.
        """
        existing_user = self.user_repo.get_user_by_id(id=id)

        # If user does not exist, raise an exception
        if existing_user is None:
            raise ValueError("User not found or logged in...")

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
        self.user_repo.update_user(existing_user)

        return UserResponse(
            id=existing_user.id,
            username=existing_user.username,
            first_name=existing_user.first_name,
            last_name=existing_user.last_name,
            salary=existing_user.salary,
            salary_rate=existing_user.salary_rate,
        )

    def delete_user(self, user: User) -> UserDelete:
        """
        Delete the provided user class.
        """
        self.user_repo.delete_user(user=user)
        return UserDelete(
            username=user.username, first_name=user.first_name, last_name=user.last_name
        )

    def refresh_user(self, user: User):
        user = self.user_repo.get_user_by_id(user.id)
        return user

    def store_user_item(self, user: User, access_token: str, item_id: str) -> Item:
        """
        This task retrieves all necessary metadata and creates an Item
        for the given access token and user.

        Args:
            user (User): User to add plaid item
            access_token (str): plaid access token associated to the item we want
            item_id (str): id of the plaid item that we're storing

        Returns:
            Item: Item that was pushed to the finance repository.
        """
        # Get item metadata from Plaid
        # TODO: potentially store request info in Redis for faster querying and reduced plaid API requests
        item_get_request = ItemGetRequest(access_token=access_token)
        item_get_response = plaid_client.item_get(
            item_get_request=item_get_request
        ).to_dict()["item"]
        # Create item
        item = Item(
            id=item_id,
            access_token=access_token,
            bank_name=item_get_response["institution_name"],
            user=user,
        )
        self.user_repo.add_user_item(item)
        logger.debug(f"Pushed item {item.id} tied to user {item.user.id}")
        return item

    def store_user_accounts(self, item: Item):
        """
        This task retreives needed metadata to create and store accounts associated to an item for a user

        Args:
            item (Item): The item the accounts we're persisting are under.

        Returns:
            None.
        """
        accounts_get_request = AccountsGetRequest(access_token=item.access_token)
        accounts: list = plaid_client.accounts_get(
            accounts_get_request=accounts_get_request
        ).to_dict()["accounts"]
        # loop through accounts, make model and save to repo
        for plaid_account in accounts:
            account = Account(
                id=plaid_account["account_id"],
                name=plaid_account["name"],
                item=item,
            )
            self.user_repo.add_user_account(account)
            logger.debug(f"Pushed account {account.id} tied to item {account.item.id}")
