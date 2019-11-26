import requests

from .. import error


class BaseInterface:

    MAX_RETRIES = 3
    TIMEOUT = 60

    def __init__(self):
        self.session = requests.sessions.Session()

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
        resp.encoding = 'utf-8'
        if resp.status_code == 401 or b'session has expired' in resp.content:
            # session expired, renew and retry
            if not self.renew_session():
                raise error.NotAuthenticated()
            return self.retry(resp.request, resp, retrying + 1)

        if resp.ok:
            return resp

        if resp.status_code == 403:
            raise error.PermissionDenied(
                f'check the role of api key: {self.api_token.key_id}'
            )
        if resp.status_code == 404:
            raise error.ResourceNotFound(f'{resp}: {resp.text}')

        if resp.status_code == 409:
            raise error.InvalidRequestData(f'{resp}: {resp.text}')
        if resp.status_code == 400:
            raise error.InvalidRequestData(f'{resp}: {resp.text}')
        # have no idea what to do now, just raise requests error
        raise error.UnwantedResponse(f'{resp}: {resp.text}')

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
