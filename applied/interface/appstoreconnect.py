from time import time

import jwt

from applied import error

from .base import BaseInterface


class ApiToken:
    def __init__(self, key_id: str, auth_key: str, issuer_id: str):
        self.key_id = key_id
        self.auth_key = auth_key
        self.issuer_id = issuer_id

    def renew_token(self):
        jwt_header = {'alg': 'ES256', 'kid': self.key_id, 'typ': 'JWT'}
        jwt_payload = {
            'iss': self.issuer_id,
            'exp': int(time()) + 1200,  # 20 mins
            'aud': f'appstoreconnect-v1',
        }
        try:
            return jwt.encode(
                jwt_payload,
                self.auth_key,
                algorithm='ES256',
                headers=jwt_header,
            ).decode()
        except ValueError:
            raise error.InvalidJWT(
                f'invalid key: {self.key_id}, issuer_id: {self.issuer_id}'
            )


class ApiSession(BaseInterface):

    ROOT_URL = 'https://api.appstoreconnect.apple.com/v1'

    def __init__(self, api_token, session_kwargs=None):
        super().__init__(session_kwargs)
        self.api_token = api_token
        self.session.headers['Accept'] = 'application/json'

        self.renew_session()

    def renew_session(self):
        self.session.headers[
            'Authorization'
        ] = f'Bearer {self.api_token.renew_token()}'
        return True

    def handle_resp(self, resp, retrying=1):
        resp.encoding = 'utf-8'
        if resp.status_code == 401:
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

    def renew_req(self, req):
        req.headers['Authorization'] = self.session.headers['Authorization']
        return req
