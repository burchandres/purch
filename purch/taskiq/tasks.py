from typing import Annotated

from taskiq import TaskiqDepends, Context
from plaid.models import ItemGetRequest, AccountsGetRequest, TransactionsSyncRequest

from purch.taskiq import broker
from purch.taskiq.dependencies import get_finance_service
from purch.plaid.client import plaid_client
from purch.domains.models import User, Item, Account, Transaction
from purch.domains.user.repository import UserRepository
from purch.domains.finance.service import FinanceService
from purch.domains.finance.schemas import ItemCreate, AccountsCreate
from purch.common.config import get_settings
from purch.common.logger import get_logger

logger = get_logger(__name__)


@broker.task(retry_on_error=True)
async def create_and_add_item_and_accounts(
    access_token: str,
    item_id: str,
    user: User,
    finance_service: Annotated[FinanceService, TaskiqDepends(get_finance_service)],
    context: Annotated[Context, TaskiqDepends()],
):
    logger.debug(
        f"Task {context.message.task_id}: adding item and accounts for user {user.id}"
    )
    # create and store item
    item = finance_service.add_item(
        ItemCreate(access_token=access_token, item_id=item_id, user=user)
    )
    # create and store associated accounts
    finance_service.add_accounts(AccountsCreate(access_token=access_token, item=item))
    logger.debug(f"done with task: {context.message.task_id}")


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


@broker.task(schedule={"cron": "0 0 * * *"})
async def sync_all_transactions():
    logger.debug("Syncing all transactions for all users within Purch...")
    settings = get_settings()
    user_repo = UserRepository(settings=settings)
    all_users = user_repo.get_all()
    # TODO: optimize this
    for user in all_users:
        for item in user.items:
            await sync_transactions.kiq(
                plaid_access_token=item.access_token,
                initial_cursor=item.transaction_cursor,
            )
    logger.debug("done running sync_all_transactions.")
