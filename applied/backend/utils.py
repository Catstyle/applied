from functools import wraps
from uuid import uuid4

from ujson import dumps

from . import MISSING


def cache(key, default=None, ttl=None):
    def wrapper(func):
        @wraps(func)
        def _(self, *args, **kwargs):
            value = self.backend.get(key)
            if value is MISSING:
                # renew
                identity = str(uuid4())
                if self.backend.request_renew(key, identity, self.TIMEOUT):
                    value = func(self, *args, **kwargs)
                    self.backend.save(key, dumps(value), ttl)
                    self.backend.finish_renew(key, identity)
                else:
                    # someone else doing renew, wait for it
                    value = self.backend.wait(key, self.TIMEOUT)
                    if value is MISSING:
                        value = default
            return value
        return _
    return wrapper
