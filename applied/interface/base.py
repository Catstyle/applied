import requests

from .. import error


class BaseInterface:

    MAX_RETRIES = 3
    TIMEOUT = 30 * 1000

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
        self.renew_req(req)
        return self.handle_resp(self.session.send(req), retrying)

    def renew_req(self, req):
        return req

    def handle_resp(self, resp, retrying=1):
        resp.encoding = 'utf-8'
        if resp.ok:
            return resp

        if resp.status_code == 401:
            # api token expired, renew token and retry
            self.renew_session()
            return self.retry(resp.request, resp, retrying + 1)

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

    def get(self, path, params=None, data=None, json=None, headers=None):
        resp = self.session.get(
            self.ensure_url(path),
            params=params, data=data, json=json, headers=headers,
        )
        return self.handle_resp(resp)

    def patch(self, path, params=None, data=None, json=None, headers=None):
        resp = self.session.patch(
            self.ensure_url(path),
            params=params, data=data, json=json, headers=headers,
        )
        return self.handle_resp(resp)

    def put(self, path, params=None, data=None, json=None, headers=None):
        resp = self.session.put(
            self.ensure_url(path),
            params=params, data=data, json=json, headers=headers,
        )
        return self.handle_resp(resp)

    def post(self, path, params=None, data=None, json=None, headers=None):
        resp = self.session.post(
            self.ensure_url(path),
            params=params, data=data, json=json, headers=headers,
        )
        return self.handle_resp(resp)

    def delete(self, path, params=None, data=None, json=None, headers=None):
        resp = self.session.delete(
            self.ensure_url(path),
            params=params, data=data, json=json, headers=headers,
        )
        return self.handle_resp(resp)
