from functools import lru_cache
from taskiq_redis import RedisStreamBroker, RedisAsyncResultBackend

from purch.utils.config import get_settings


@lru_cache
def get_taskiq_broker():
    settings = get_settings()
    redis_url = settings.get_redis_url()
    broker = RedisStreamBroker(
        url=redis_url
    ).with_result_backend(
        RedisAsyncResultBackend(redis_url=redis_url)
    )
    return broker
