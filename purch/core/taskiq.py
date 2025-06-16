import os
from taskiq import TaskiqScheduler, SimpleRetryMiddleware, InMemoryBroker
from taskiq_redis import (
    RedisStreamBroker,
    RedisAsyncResultBackend,
    ListRedisScheduleSource,
)

from purch.utils.config import get_settings


def setup_taskiq_broker_and_scheduler():
    settings = get_settings()
    # Check for test environment first, before loading settings
    if settings.POSTGRES_DATABASE.startswith("test_db_"):
        # Use InMemoryBroker for testing
        broker = InMemoryBroker()
        scheduler = TaskiqScheduler(broker=broker, sources=[])
        return broker, scheduler

    # Production/Development Redis setup
    broker = (
        RedisStreamBroker(url=settings.get_redis_url())
        .with_result_backend(
            RedisAsyncResultBackend(redis_url=settings.get_redis_url())
        )
        .with_middlewares(SimpleRetryMiddleware(default_retry_count=3))
    )

    redis_source = ListRedisScheduleSource(url=settings.get_redis_url())

    scheduler = TaskiqScheduler(broker=broker, sources=[redis_source])

    return broker, scheduler
