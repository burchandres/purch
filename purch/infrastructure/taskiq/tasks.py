from concurrent import futures
from typing import Annotated

from taskiq import TaskiqDepends, Context

from purch.infrastructure.taskiq import broker
from purch.common.dependencies import (
    get_budget_service,
    get_user_repository,
    get_user_service
)
from purch.domains import UserService, BudgetService
from purch.domains.models import User, Item
from purch.domains.user.repository import UserRepository
from purch.common.logger import get_logger
from purch.common.config import get_settings, Settings

logger = get_logger(__name__)


@broker.task(retry_on_error=True)
def store_item(
    access_token: str,
    item_id: str,
    user: User,
    finance_service: Annotated[UserService, TaskiqDepends(get_user_service)],
):
    """
    Taskiq wrapper task for the FinanceService.store_user_item() method.

    Args:
        access_token (str): Plaid provided access token of the item
        item_id (str): id of the plaid item
        user (User): User the item is connected to

    Returns:
        Item: The item created and stored.
    """
    # create and store item
    item = finance_service.store_user_item(
        access_token=access_token, item_id=item_id, user=user
    )
    return item


@broker.task(retry_on_error=True)
def store_accounts(
    item: Item,
    user_service: Annotated[UserService, TaskiqDepends(get_user_service)],
):
    """
    Taskiq wrapper class for FinanceService.store_user_accounts() method.

    Args:
        access_token (str): Plaid provided access token of the item
    """
    # create and store accounts
    user_service.store_user_accounts(item)


@broker.task(retry_on_error=True)
async def sync_transactions(
    user: User,
    budget_service: Annotated[BudgetService, TaskiqDepends(get_budget_service)],
    context: Annotated[Context, TaskiqDepends()],
    settings: Annotated[Settings, TaskiqDepends(get_settings)],
):
    """
    This retrieves all output from the /transactions/sync endpoint of Plaid.

    We get three categories of transactions with this:

    - added: All new transactions since last time
    - modified: All prior new transactions that had some aspect of their model change (usually description update or amount update)
        - All transactions in the modified section would just replaced their corresponding rows (identifiable via transaction_id) in the database
    - removed: Transactions that were negated
        - Is just a list of dictionaries with a single key/value pair of (transaction_id: transaction_id_value)

    Args:
        user (User): the user to sync all transactions for
        finance_service (FinanceService): finance service object to leverage for doing all heavy work of syncing transactions

    Returns:
        None. Syncs to postgres.
    """
    # TODO: figure out how to rewrite this so we can requeue futures that fail
    with futures.ThreadPoolExecutor(
        max_workers=settings.MAX_CONCURRENT_WORKER_NUM
    ) as executor:
        submitted_futures = {
            executor.submit(budget_service.sync_transactions, item): item
            for item in user.items
        }

        for future in futures.as_completed(submitted_futures):
            item = submitted_futures[future]
            try:
                future.result()
                logger.debug(
                    f"Task {context.message.task_id}: successfully synced transactions for item {item.id} for user {user.id}"
                )
            except Exception as e:
                logger.warning(
                    f"Task {context.message.task_id}: error completing sync transaction task for item {item.id} for user {user.id}."
                )


@broker.task(schedule={"cron": "0 0 * * *"})
async def sync_all_transactions(
    context: Annotated[Context, TaskiqDepends()],
    user_repo: Annotated[UserRepository, TaskiqDepends(get_user_repository)],
):
    logger.debug(
        f"Task {context.message.task_id}: Syncing all transactions for all users within Purch..."
    )
    all_users = user_repo.get_all_users()
    for user in all_users:
        await sync_transactions.kiq(user=user)
    logger.debug(
        f"Task {context.message.task_id}: done firing off tasks for syncing transactions for all users within Purch"
    )
