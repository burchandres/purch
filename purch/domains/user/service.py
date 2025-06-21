from plaid.models import AccountsGetRequest, ItemGetRequest

from purch.domains.user.repository import UserRepository
from purch.domains.models import User, Item, Account
from purch.common.logger import get_logger
from purch.infrastructure.plaid.client import plaid_client

logger = get_logger(__name__)


class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def refresh_user(self, user: User):
        user = self.user_repo.get(user.id)
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
        self.item_repo.add(item)
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
            self.account_repo.add(account)
            logger.debug(f"Pushed account {account.id} tied to item {account.item.id}")
