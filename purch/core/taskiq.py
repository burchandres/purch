from functools import lru_cache
from taskiq_redis import RedisStreamBroker, RedisAsyncResultBackend

from purch.utils.config import get_settings


@lru_cache
def get_taskiq_broker():
    settings = get_settings()
    broker = RedisStreamBroker()
