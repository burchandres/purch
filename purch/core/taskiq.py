from functools import lru_cache
from taskiq import TaskiqScheduler, SimpleRetryMiddleware
from taskiq_redis import (
    RedisStreamBroker,
    RedisAsyncResultBackend,
    RedisScheduleSource,
)

from purch.utils.config import get_settings


@lru_cache
def setup_taskiq_broker_and_scheduler():
    settings = get_settings()

    broker = RedisStreamBroker(url=settings.get_redis_url()).with_result_backend(
        RedisAsyncResultBackend(redis_url=settings.get_redis_url())
    ).with_middlewares(
        SimpleRetryMiddleware(default_retry_count=3)
    )

    redis_source = RedisScheduleSource(url=settings.get_redis_url())

    scheduler = TaskiqScheduler(broker=broker, sources=[redis_source])

    return broker, scheduler
