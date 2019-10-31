from time import time, sleep
from threading import Thread

from redis import Redis

from applied import logger
from .base import BaseBackend, MISSING


class RedisBackend(BaseBackend):

    TYPE = 'Redis'
    DATA_UPDATED_CHANNEL = 'DATA_UPDATED'

    def __init__(self, ttl, rdb: Redis = None):
        super().__init__(ttl)
        self.rdb = rdb or Redis()
        self.subscriber = Thread(target=self.subscribe_channel)
        self.subscriber.daemon = True
        self.subscriber.start()

    @property
    def backend_data(self):
        return {
            'type': self.TYPE,
            **self.rdb.connection_pool.connection_kwargs,
        }

    def subscribe_channel(self):
        ps = self.rdb.pubsub(ignore_subscribe_messages=True)
        ps.subscribe(self.DATA_UPDATED_CHANNEL)
        for message in ps.listen():
            logger.debug(f'subscribe_channel received: {message}')
            data = message['data']
            if data == b'FINISHED':
                break
            self.fetch_value(data)

    def fetch_value(self, key: str):
        value = self.rdb.get(key)
        if value is not None:
            self.load_data(key, value)

    def save(self, key: str, value: str, ttl: int = None, publish=True):
        if ttl is not None and not ttl:
            ttl = self.ttl
        self.rdb.set(key, value, px=ttl)
        if publish:
            self.rdb.publish(self.DATA_UPDATED_CHANNEL, key)

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

    def __del__(self):
        self.subscriber.stop()
