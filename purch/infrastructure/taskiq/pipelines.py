from taskiq_pipelines import Pipeline

from purch.infrastructure.taskiq import broker
from purch.infrastructure.taskiq.tasks import store_item, store_accounts


item_account_storage_pipeline = Pipeline(broker, store_item).call_next(store_accounts)
