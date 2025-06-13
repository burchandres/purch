from plaid.models import ItemGetRequest, AccountsGetRequest

from purch.core import broker
from purch.core.models import User, Item, Account
from purch.finance.plaid import plaid_client
from purch.finance.repository import FinanceRepository
from purch.utils.config import get_settings
from purch.utils.logger import get_logger

logger = get_logger(__name__)


@broker.task()
async def store_item(access_token: str, item_id: str, user: User) -> Item:
    """
    This task retrieves all necessary metadata to create an Item for the given access token for the user.

    Args:
        access_token (str): The access token to store that was given by exchanging for the public token.
        item_id (str): The id of the item we're creating.
        user (User): The user that all of this is associated under.

    Returns:
        Item: The item that was pushed to postgres.
    """
    settings = get_settings()
    # get item metadata first; TODO: store info in redis for faster lookup later if possible
    item_request = ItemGetRequest(access_token=access_token)
    item_response = plaid_client.item_get(item_request).to_dict()["item"]
    # create Item
    item = Item(
        id=item_id,
        access_token=access_token,
        bank_name=item_response["institution_name"],
        user=user,
    )
    logger.debug(f"Pushed item {item.id} to postgres.")
    # push to postgres
    finance_repo = FinanceRepository(settings=settings)
    finance_repo.add(item)
    return item


@broker.task()
async def store_accounts(access_token: str, item: Item):
    """
    Stores accounts associated to the item tied to the given item_id in the database.

    Args:
        access_token (str): The Plaid access token tied to an item.
        item (Item): The item that all accounts are associated to.

    Returns:
        None.
    """
    settings = get_settings()
    # get accounts' metadata
    accounts_request = AccountsGetRequest(access_token=access_token)
    accounts: list = plaid_client.accounts_get(accounts_request).to_dict()["accounts"]
    # loop through above accounts
    finance_repo = FinanceRepository(settings=settings)
    for plaid_account in accounts:
        # create Account model
        account = Account(
            id=plaid_account["account_id"], name=plaid_account["name"], item=item
        )
        finance_repo.add(account)
        logger.debug(
            f"Pushed account {account.id} tied to item {account.item.id} to postgres."
        )
