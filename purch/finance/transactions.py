import time
import plaid

from plaid.model.transactions_sync_request import TransactionsSyncRequest

from finance.plaid import plaid_client
from finance.models import Transaction

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
def get_transactions(plaid_access_token: str) -> dict[str, list[Transaction]]:
    """
    This retrieves all output from the /transactions/sync endpoint of Plaid.

    We get three categories of transactions with this:

    - added: All new transactions since last time
    - modified: All prior new transactions that had some aspect of their model change (usually description update or amount update)
        - All transactions in the modified section would just replaced their corresponding rows (identifiable via transaction_id) in the database
    - removed: Transactions that were negated
        - Is just a list of dictionaries with a single key/value pair of (transaction_id: <transaction_id_value>)

    Args:
        plaid_access_token (str): Plaid generated access token after connecting bank account to link (i.e. creating a plaid item) to authorize plaid API requests.

    Returns:
        list[Transaction]: All transactions we get from hitting /transactions/sync
    """
    added = []
    modified = []
    removed = []
    cursor = ""
    has_more = True
    try:
        # Iterate through each page of new transaction updates for item
        while has_more:
            request = TransactionsSyncRequest(
                access_token=plaid_access_token,
                cursor=cursor,
            )
            response = plaid_client.transactions_sync(request).to_dict()
            cursor = response["next_cursor"]
            # TODO: USE WEBHOOKS TO LISTEN FOR WHEN DATA IS UPDATED AND HAVE IT RUN IN THE BACKGROUND
            if cursor == "":
                time.sleep(2)
                continue
            # If cursor is not an empty string, we got results,
            # so add this page of results
            added.extend(response["added"])
            modified.extend(response["modified"])
            removed.extend(response["removed"])
            has_more = response["has_more"]

        return {"added": added, "modified": modified, "removed": removed}

    except plaid.ApiException:
        raise RuntimeError("Unable to pull transactions currently.")
