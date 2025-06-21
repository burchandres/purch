import taskiq_fastapi

from taskiq import TaskiqScheduler, SimpleRetryMiddleware
from taskiq_redis import (
    RedisStreamBroker,
    RedisAsyncResultBackend,
    ListRedisScheduleSource,
)
from taskiq_pipelines.middleware import PipelineMiddleware

from purch.common.config import get_settings


def setup_taskiq_broker_and_scheduler():
    settings = get_settings()
    # broker setup
    broker = (
        RedisStreamBroker(url=settings.get_redis_url())
        .with_result_backend(
            RedisAsyncResultBackend(redis_url=settings.get_redis_url())
        )
        .with_middlewares(
            SimpleRetryMiddleware(default_retry_count=3), PipelineMiddleware()
        )
    )
    # scheduler setup
    redis_source = ListRedisScheduleSource(url=settings.get_redis_url())

    scheduler = TaskiqScheduler(broker=broker, sources=[redis_source])

    return broker, scheduler


broker, scheduler = setup_taskiq_broker_and_scheduler()

taskiq_fastapi.init(broker, "purch.main:app")
