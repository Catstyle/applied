import requests

from .. import error


class BaseInterface:

    MAX_RETRIES = 3
    TIMEOUT = 60

    def __init__(self, session_kwargs: dict = None):
        self.session = requests.sessions.Session()
        session_kwargs = session_kwargs or {}
        for attr in session_kwargs.keys() & set(self.session.__attrs__):
            setattr(self.session, attr, session_kwargs[attr])

    def renew_session(self):
        raise NotImplementedError

    def ensure_url(self, path):
        if path.startswith('http://') or path.startswith('https://'):
            return path
        return f'{self.ROOT_URL}{path}'

    def retry(self, req, resp, retrying):
        if retrying > self.MAX_RETRIES:
            raise error.MaxRetries(
                f'exceed max retries for {req.method} {req.path_url}, '
                f'last resp, {resp.status_code} {resp.content}'
            )
        req = self.renew_req(req)
        return self.handle_resp(self.session.send(req), retrying)

    def renew_req(self, req):
        return req

    def handle_resp(self, resp, retrying=1):
        raise NotImplementedError('handle_resp')

    def get(self, path, **kwargs):
        resp = self.session.get(
            self.ensure_url(path),
            timeout=kwargs.pop('timeout', self.TIMEOUT),
            **kwargs,
        )
        return self.handle_resp(resp)

    def patch(self, path, data=None, json=None, **kwargs):
        resp = self.session.patch(
            self.ensure_url(path),
            data=data,
            json=json,
            timeout=kwargs.pop('timeout', self.TIMEOUT),
            **kwargs,
        )
        return self.handle_resp(resp)

    def put(self, path, data=None, json=None, **kwargs):
        resp = self.session.put(
            self.ensure_url(path),
            data=data,
            json=json,
            timeout=kwargs.pop('timeout', self.TIMEOUT),
            **kwargs,
        )
        return self.handle_resp(resp)

    def post(self, path, data=None, json=None, **kwargs):
        resp = self.session.post(
            self.ensure_url(path),
            data=data,
            json=json,
            timeout=kwargs.pop('timeout', self.TIMEOUT),
            **kwargs,
        )
        return self.handle_resp(resp)

    def delete(self, path, **kwargs):
        resp = self.session.delete(
            self.ensure_url(path),
            timeout=kwargs.pop('timeout', self.TIMEOUT),
            **kwargs,
        )
        return self.handle_resp(resp)
