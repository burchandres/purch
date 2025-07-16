from plaid.models import TransactionsSyncRequest

from purch.domains.models import Item, Transaction
from purch.domains.budget.repository import BudgetRepository
from purch.domains.budget.schemas import TransactionUpdate
from purch.common.logger import get_logger
from purch.infrastructure.plaid.client import plaid_client

logger = get_logger(__name__)


class BudgetService:
    def __init__(self, budget_repo: BudgetRepository | None = None):
        self.budget_repo = budget_repo or BudgetRepository()

    # TODO: find a way to optimize this
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
            self.budget_repo.add_new_transactions(
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
            self.budget_repo.update_transactions(
                [
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
                    )
                    for txn in transactions_sync_response["modified"]
                ]
            )
            # delete transactions flagged as removed by plaid
            logger.debug(f"removing transactions for item {item.id}")
            self.budget_repo.delete_transactions(
                [txn["transaction_id"] for txn in transactions_sync_response["removed"]]
            )
