from typing import Any, Union

from cachetools import TTLCache
import ujson as json

MISSING = object()


class BaseBackend:

    TIMEOUT = 30 * 1000

    def __init__(self, ttl):
        self.ttl = ttl
        self.values = TTLCache(maxsize=1024, ttl=ttl / 1000)

    def load_data(self, key: str, data):
        try:
            self.values[key] = json.loads(data)
        except (TypeError, ValueError):
            self.values[key] = data

    def fetch_value(self, key: str):
        pass

    def get(self, key: str) -> Union[bytes, dict]:
        if key not in self.values:
            self.fetch_value(key)
        try:
            # still maybe empty
            return self.values[key]
        except KeyError:
            return MISSING

    def clear(self, key: str):
        self.values.pop(key, None)

    def save(self, key: str, value: Any, ttl: int = None):
        self.values[key] = value

    def wait(self, key: str, timeout: int):
        # same as get in BaseBackend
        return self.get(key)

    def request_renew(self, key: str, value: str, timeout: int):
        return True

    def finish_renew(self, key: str, value: str):
        pass


class TTLCacheBackend(BaseBackend):

    TYPE = 'TTLCache'

    @property
    def backend_data(self):
        return {
            'type': self.TYPE,
            'ttl': self.ttl,
        }
