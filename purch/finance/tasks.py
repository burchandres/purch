from plaid.models import ItemGetRequest, AccountsGetRequest, TransactionsSyncRequest

from purch.core import broker
from purch.core.models import User, Item, Account, Transaction
from purch.finance.plaid import plaid_client
from purch.finance.repository import FinanceRepository
from purch.utils.config import get_settings
from purch.utils.logger import get_logger

logger = get_logger(__name__)


@broker.task(retry_on_error=True)
async def create_and_store_item_and_accounts(access_token: str, item_id: str, user: User):
    # create and store item
    store_item_task = await store_item.kiq(
        access_token=access_token,
        item_id=item_id,
        user=user
    )
    # wait for above task to finish
    store_item_result = await store_item_task.wait_result()
    if store_item_result.is_err:
        raise RuntimeError(f"error creating and storing item {item_id} for user {user.id}")
    # fire off task to create and store accounts associated with above item
    await store_accounts.kiq(access_token=access_token, item=store_item_result.return_value)
    logger.debug(f"Success creating and storing items for user {user.id}")


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
    logger.debug(f"Pushed item {item.id} tied to user {user.id}.")
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
            f"Pushed account {account.id} tied to item {account.item.id}."
        )


# Some notes to consider when dealing with transactions...

# ADDED/MODIFIED -- anything in modified is to replace the transaction with the same transaction id in purch.transactions
# - 'authorized_date' field is when the card was swiped. The 'date' field is when it posted to the credit card's balance.
#    - If 'authorized_date' isn't present then use 'date' -- BOTH ARE FORMATTED IN ISO 8601 (i.e. YYYY-MM-DD)
# - `account_id` field that we want to use to associate it to said account
# - 'merchant_name' is the human readable version of the merchant the transaction happened with (i.e. "Burger King")
# - 'personal_finance_category' which is a dict/json with a 'primary' category (broad) and 'secondary' (more refined)
# - 'pending' a bool representing if the transaction is yet to be settled
# - 'pending_transaction_id' I believe is NULL for added and populated for modified if the original added version's 'pending' was set to True
# - 'payment_channel' str of the following possible values: "online", "in store" or "other"
# - 'iso_currency_code' is the currency code (i.e. 'USD')

# REMOVED -- these are transactions to be removed from purch.transactions table
# - 'transaction_id' the id of the removed transaction
# - 'account_id' the id the removed transaction is associated with

# Separate from those
# - 'next_cursor' used in future requests if plaid had more new data to send us but couldn't with the limit we had
# - 'has_more' bool represnting if plaid has more data to send to us
# - 'request_id' used for troubleshooting (case sensitive)
# - 'transaction_update_status' (VERY IMPORTANT)


# TODO: potentially return a dict[str, pl.DataFrame] (i.e. with the keys 'added', 'modified', 'removed')
# TODO: upon user with purch and plaid, and we've stored the plaid_access_token we then go in and pull transactions
#       then in the background, every 24 hours pull transactions for the day and update stuff
@broker.task()
async def sync_transactions(
    plaid_access_token: str, initial_cursor: str
) -> dict[str, list[Transaction]]:
    """
    This retrieves all output from the /transactions/sync endpoint of Plaid.

    We get three categories of transactions with this:

    - added: All new transactions since last time
    - modified: All prior new transactions that had some aspect of their model change (usually description update or amount update)
        - All transactions in the modified section would just replaced their corresponding rows (identifiable via transaction_id) in the database
    - removed: Transactions that were negated
        - Is just a list of dictionaries with a single key/value pair of (transaction_id: transaction_id_value)

    Args:
        plaid_access_token (str): Plaid generated access token after connecting bank account to link (i.e. creating a plaid item) to authorize plaid API requests.
        initial_cursor (str): Cursor marking last point in time we want to call the transactions/sync endpoint at -- these are per item

    Returns:
        dict: All transactions we get from hitting /transactions/sync with keys:
            - 'added' -> list of newly added transactions
            - 'modified' -> list of modified transactions
            - 'removed' -> list of transaction ids that have been removed
    """
    added = []
    modified = []
    removed = []
    cursor = initial_cursor
    has_more = True
    # Iterate through each page of new transaction updates for item
    while has_more:
        request = TransactionsSyncRequest(
            access_token=plaid_access_token,
            cursor=cursor,
        )
        response = plaid_client.transactions_sync(request).to_dict()
        cursor = response["next_cursor"]
        # TODO: USE WEBHOOKS TO LISTEN FOR WHEN DATA IS UPDATED AND HAVE IT RUN IN THE BACKGROUND
        # if cursor == "":
        #     time.sleep(2)
        #     continue
        # If cursor is not an empty string, we got results,
        # so add this page of results
        added.extend(response["added"])
        modified.extend(response["modified"])
        removed.extend(response["removed"])
        has_more = response["has_more"]

    return {"added": added, "modified": modified, "removed": removed}, cursor

