import asyncio

from plaid.models import ItemGetRequest, AccountsGetRequest, TransactionsSyncRequest

from purch.infrastructure.plaid.client import plaid_client
from purch.domains.models import Item, Account, Transaction
from purch.domains.finance.repository import (
    ItemRepository,
    AccountRepository,
    TransactionRepository,
)
from purch.domains.finance.schemas import (
    AccountCreate,
    ItemCreate,
    TransactionUpdate,
)
from purch.common.logger import get_logger


logger = get_logger(__name__)

# Some notes to consider when dealing with transactions...

# ADDED/MODIFIED -- anything in modified is to replace the transaction with the same transaction id in purch.transactions
# - 'authorized_date' field is when the card was swiped. The 'date' field is when it posted to the credit card's balance.
#    - If 'authorized_date' isn't present then use 'date' -- BOTH ARE FORMATTED IN ISO 8601 (i.e. YYYY-MM-DD)
# - 'amount' transaction amount
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
# - 'transaction_update_status' (VERY IMPORTANT) tells us how much of a user's transaction history is ready to be pulled


class FinanceService:
    def __init__(self):
        self.item_repo = ItemRepository()
        self.account_repo = AccountRepository()
        self.transaction_repo = TransactionRepository()

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
        self.item_repo.add(item)
        logger.debug(f"Pushed item {item.id} tied to user {item.user.id}")
        return item

    def add_accounts(self, accounts_create: AccountCreate):
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
            self.account_repo.add(account)
            logger.debug(f"Pushed account {account.id} tied to item {account.item.id}")

    def sync_transactions(self, item: Item):
        """
        Pulls all transactions from for the given access_token. Using item.transaction_cursor

        Args:
            item (Item): The item for which we pull transactions

        Returns:
            None
        """
        logger.debug(f"syncing transactions for item {item.id}")
        cursor = item.transaction_cursor
        has_more = True
        # Iterate through each page of new transaction updates for item
        while has_more:
            transactions_sync_request = TransactionsSyncRequest(
                access_token=item.access_token, cursor=cursor
            )
            transactions_sync_response = plaid_client.transactions_sync(
                transactions_sync_request
            ).to_dict()
            cursor = transactions_sync_response["next_cursor"]
            has_more = transactions_sync_response["has_more"]

            # map added transaction json blob to Transaction class and push to transaction repo
            logger.debug(f"adding new transactions for item {item.id}")
            self.transaction_repo.add_all(
                [
                    Transaction(
                        id=txn["transaction_id"],
                        account_id=txn["account_id"],
                        # TODO: use secondary category if/when needed
                        category=txn["personal_finance_category"]["primary"],
                        authorized_date=txn["authorized_date"]
                        if "authorized_date" in txn
                        else txn["date"],
                        settled_date=txn["date"],
                        merchant_name=txn["merchant_name"],
                        amount=txn["amount"],
                        currency_code=txn["iso_currency_code"],
                        pending=txn["pending"],
                        account=list(
                            filter(lambda x: x.id == txn["account_id"], item.accounts)
                        )[0],
                    )
                    for txn in transactions_sync_response["added"]
                ]
            )
            # map modified transaction json blob to Transaction class and update as you go
            # TODO: optimize this if possible
            logger.debug(f"updating transactions for item {item.id}")
            for txn in transactions_sync_response["modified"]:
                self.transaction_repo.update(
                    TransactionUpdate(
                        id=txn["transaction_id"],
                        pending_transaction_id=txn["pending_transaction_id"],
                        account_id=txn["account_id"],
                        # TODO: use secondary category if/when needed
                        category=txn["personal_finance_category"]["primary"],
                        authorized_date=txn["authorized_date"]
                        if "authorized_date" in txn
                        else txn["date"],
                        settled_date=txn["date"],
                        merchant_name=txn["merchant_name"],
                        amount=txn["amount"],
                        currency_code=txn["iso_currency_code"],
                        pending=txn["pending"],
                        account=list(
                            filter(lambda x: x.id == txn["account_id"], item.accounts)
                        )[0],
                    )
                )
            # delete transactions flagged as removed by plaid
            logger.debug(f"removing transactions for item {item.id}")
            for txn in transactions_sync_response["removed"]:
                self.transaction_repo.delete(id=txn["transaction_id"])
