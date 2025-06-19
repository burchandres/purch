from plaid.models import ItemGetRequest, AccountsGetRequest, TransactionsSyncRequest

from purch.plaid.client import plaid_client
from purch.domains.models import User, Item, Account, Transaction
from purch.domains.finance.repository import FinanceRepository
from purch.domains.finance.schemas import ItemCreate, AccountsCreate
from purch.common.logger import get_logger


logger = get_logger(__name__)


class FinanceService:
    def __init__(self):
        self.finance_repo = FinanceRepository()

    def add_item(self, item_create: ItemCreate) -> Item:
        """
        This task retrieves all necessary metadata and creates an Item
        for the given access token and user.

        Args:
            item_create (ItemCreate): Contains access_token, item_id and associated user for the item to create

        Returns:
            Item: Item that was pushed to the finance repository.
        """
        # Get item metadata from Plaid
        # TODO: potentially store request info in Redis for faster querying and reduced plaid API requests
        item_get_request = ItemGetRequest(access_token=item_create.access_token)
        item_get_response = plaid_client.item_get(
            item_get_request=item_get_request
        ).to_dict()["item"]
        # Create item
        item = Item(
            id=item_create.item_id,
            access_token=item_create.access_token,
            bank_name=item_get_response["institution_name"],
            user=item_create.user,
        )
        self.finance_repo.add(item)
        logger.debug(f"Pushed item {item.id} tied to user {item.user.id}")
        return item

    def add_accounts(self, accounts_create: AccountsCreate):
        """
        This task retreives needed metadata to create and store accounts associated to an item for a user

        Args:
            accounts_create (AccountsCreate): Contains the access_token and item for the account

        Returns:
            None.
        """
        accounts_get_request = AccountsGetRequest(
            access_token=accounts_create.access_token
        )
        accounts: list = plaid_client.accounts_get(
            accounts_get_request=accounts_get_request
        ).to_dict()["accounts"]
        # loop through accounts, make model and save to repo
        for plaid_account in accounts:
            account = Account(
                id=plaid_account["account_id"],
                name=plaid_account["name"],
                item=accounts_create.item,
            )
            self.finance_repo.add(account)
            logger.debug(f"Pushed account {account.id} tied to item {account.item.id}")
