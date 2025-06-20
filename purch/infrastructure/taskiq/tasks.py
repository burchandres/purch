from concurrent import futures
from typing import Annotated

from taskiq import TaskiqDepends, Context

from purch.infrastructure.taskiq import broker
from purch.infrastructure.taskiq.dependencies import (
    get_finance_service,
    get_user_repository,
)
from purch.domains.models import User
from purch.domains.user.repository import UserRepository
from purch.domains.finance.service import FinanceService
from purch.domains.finance.schemas import ItemCreate, AccountCreate
from purch.common.logger import get_logger
from purch.common.config import get_settings, Settings

logger = get_logger(__name__)


@broker.task(retry_on_error=True)
def create_and_add_item_and_accounts(
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
    finance_service.add_accounts(AccountCreate(access_token=access_token, item=item))
    logger.debug(f"Task {context.message.task_id}: done.")


@broker.task(retry_on_error=True)
async def sync_transactions(
    user: User,
    finance_service: Annotated[FinanceService, TaskiqDepends(get_finance_service)],
    context: Annotated[Context, TaskiqDepends()],
    settings: Annotated[Settings, TaskiqDepends(get_settings)]
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
    """
    # TODO: figure out how to rewrite this so we can requeue futures that fail
    with futures.ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_WORKER_NUM) as executor:
        submitted_futures = {
            executor.submit(finance_service.sync_transactions, item): item
            for item in user.items
        }

        for future in futures.as_completed(submitted_futures):
            item = submitted_futures[future]
            try:
                future.result()
                logger.debug(
                    f"Task {context.message.task_id}: Successfully synced transactions for item {item.id} for user {user.id}"
                )
            except Exception as e:
                logger.warning(
                    f"Task {context.message.task_id}: Error completing sync transaction task for item {item.id} for user {user.id}."
                )


@broker.task(schedule={"cron": "0 0 * * *"})
async def sync_all_transactions(
    context: Annotated[Context, TaskiqDepends()],
    user_repo: Annotated[UserRepository, TaskiqDepends(get_user_repository)],
):
    logger.debug(
        f"Task {context.message.task_id}: Syncing all transactions for all users within Purch..."
    )
    all_users = user_repo.get_all()
    for user in all_users:
        await sync_transactions.kiq(user=user)
    logger.debug(
        f"Task {context.message.task_id}: done firing off tasks for syncing transactions for all users within Purch"
    )
