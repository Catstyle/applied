from time import time, sleep

from redis import Redis

from .base import BaseBackend, MISSING


class RedisBackend(BaseBackend):

    TYPE = 'Redis'

    def __init__(self, ttl, rdb: Redis = None):
        super().__init__(ttl)
        self.rdb = rdb or Redis()

    @property
    def backend_data(self):
        return {
            'type': self.TYPE,
            **self.rdb.connection_pool.connection_kwargs,
        }

    def fetch_value(self, key: str):
        value = self.rdb.get(key)
        if value is not None:
            self.load_data(key, value)

    def save(self, key: str, value: str, ttl: int = None):
        if ttl is not None and not ttl:
            ttl = self.ttl
        self.values[key] = value
        self.rdb.set(key, value, px=ttl)

    def wait(self, key: str, timeout: int):
        end = int(time()) * 1000 + timeout
        value = self.rdb.get(key)
        while value is None and int(time()) * 1000 < end:
            sleep(1)
            value = self.rdb.get(key)

        if value is not None:
            self.load_data(key, value)
            return self.values[key]
        else:
            return MISSING

    def request_renew(self, key: str, value: str, timeout: int):
        return self.rdb.set(key, value, px=timeout, nx=True)

    def finish_renew(self, key: str, value: str):
        if self.rdb.get(key) == value:
            self.rdb.delete(key)
