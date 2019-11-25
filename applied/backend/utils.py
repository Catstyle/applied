from functools import wraps
from uuid import uuid4

from ujson import dumps

from . import MISSING


def cache(key_format, default=None, ttl=None):
    def wrapper(func):
        @wraps(func)
        def _(self, *args, **kwargs):
            key = key_format.format(self=self, *args, **kwargs)
            value = self.backend.get(key)
            if value is MISSING:
                backend = self.backend
                # renew
                identity = str(uuid4())
                if backend.request_renew(key, identity, backend.TIMEOUT):
                    value = func(self, *args, **kwargs)
                    backend.save(key, dumps(value), ttl)
                    backend.finish_renew(key, identity)
                else:
                    # someone else doing renew, wait for it
                    value = backend.wait(key, backend.TIMEOUT)
                    if value is MISSING:
                        value = default
            return value

        return _

    return wrapper
