from time import time

import jwt

from applied.error import InvalidJWT

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
            raise InvalidJWT(
                f'invalid key: {self.key_id}, issuer_id: {self.issuer_id}'
            )


class ApiSession(BaseInterface):

    ROOT_URL = 'https://api.appstoreconnect.apple.com/v1'

    def __init__(self, api_token):
        super().__init__()
        self.api_token = api_token
        self.session.headers['Accept'] = 'application/json'

        self.renew_session()

    def renew_session(self):
        self.session.headers[
            'Authorization'
        ] = f'Bearer {self.api_token.renew_token()}'
        return True

    def renew_req(self, req):
        req.headers['Authorization'] = self.session.headers['Authorization']
        return req
