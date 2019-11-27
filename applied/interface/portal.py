import pickle
from uuid import uuid4
from requests.cookies import merge_cookies
from typing import Callable

from applied import logger
from .. import error
from ..backend import MISSING, TTLCacheBackend, cache

from .base import BaseInterface


class PortalSession(BaseInterface):

    DEV_QH65B2 = 'https://developer.apple.com/services-account/QH65B2'
    DEV_V1 = 'https://developer.apple.com/services-account/v1'
    APC_IRIS_V1 = 'https://appstoreconnect.apple.com/iris/v1'
    APC_OLYMPUS_V1 = 'https://appstoreconnect.apple.com/olympus/v1'

    def __init__(
        self,
        username: str,
        password: str,
        two_factor_callback: Callable,
        backend=None,
    ):
        super().__init__()
        if not (username and password):
            raise error.InvalidAuthCredential(username, password)
        self.username = username
        self.password = password

        self.backend = backend or TTLCacheBackend(ttl=600000)  # 10 mins
        self.olympus_session = {}
        self._two_factor_callback = two_factor_callback

        self.load_cookies_from_backend()

    @property
    def is_session_valid(self):
        resp = self.session.get(f'{self.APC_OLYMPUS_V1}/session')
        if resp.ok:
            self.load_olympus_session(resp.json())
            return True
        return False

    @property
    def team_id(self):
        if not hasattr(self, '_team_id'):
            teams = self.list_teams()
            if not teams:
                raise error.MissingTeamMembership(
                    f'user {self.username} does not has access to any teams '
                    'with an active membership'
                )
            elif len(teams) > 1:
                logger.warn(
                    f'user {self.username} has {len(teams)} teams, using first'
                )
            self._team_id = teams[0]['teamId']
        return self._team_id

    @property
    @cache('auth_service_key', default='', ttl=3600000)
    def auth_service_key(self):
        resp = self.session.get(
            f'{self.APC_OLYMPUS_V1}/app/config'
            '?hostname=itunesconnect.apple.com'
        )
        if not resp.ok:
            raise error.UnwantedResponse('service key is missing')
        return resp.json()['authServiceKey']

    @cache('{self.username}_list_teams', default=[])
    def list_teams(self):
        resp = self.post(f'{self.DEV_QH65B2}/account/listTeams.action')
        return resp.json()['teams']

    @cache('{self.username}_get_teams', default=[])
    def get_teams(self):
        resp = self.post(f'{self.DEV_QH65B2}/account/getTeams')
        return resp.json()['teams']

    def load_olympus_session(self, data):
        self.olympus_session = data

    def login(self):
        self.load_cookies_from_backend()
        if not self.is_session_valid:
            return self.do_login()
        return True

    def do_login(self):
        resp = self.send_login_request()
        username = self.username
        logger.debug(
            f'{username} send_login_request, resp code: {resp.status_code}, '
            f'has myacinfo: {"myacinfo" in self.session.cookies}, '
            f'has authType: {"authType" in resp.text}'
        )
        if resp.ok and 'myacinfo' in self.session.cookies:
            self.store_session()
            self.load_cookies_from_backend()
            return True

        if resp.status_code == 409 or 'authType' in resp.text:
            # 2 step/factor is enabled for this account
            lock_name = f'renew_{username}'
            value = str(uuid4())
            backend = self.backend
            if backend.request_renew(lock_name, value, 90000):
                logger.debug(f'{username} request_renew, {lock_name} {value}')
                self.handle_two_step_or_factor(resp)
                backend.finish_renew(lock_name, value)
                backend.save(f'done_renew_{username}', 1, 10000)
            else:
                # someone else doing renew
                logger.debug(f'{username} wait renew')
                backend.wait(f'done_renew_{username}', 15000)
                self.load_cookies_from_backend()
            return self.is_session_valid
        return False

    renew_session = do_login

    def load_cookies_from_backend(self):
        value = self.backend.get(f'{self.username}.cookies')
        if value is MISSING:
            return False
        self.session.cookies = merge_cookies(
            self.session.cookies, pickle.loads(value)
        )

    def store_session(self):
        logger.debug(f'store_session: {self.session.cookies}')
        # set ttl = None to disable ttl
        self.backend.save(
            f'{self.username}.cookies',
            pickle.dumps(self.session.cookies),
            ttl=None,
        )

    def send_login_request(self):
        # below are from `fastlane/spaceship`

        # The below workaround is only needed for 2 step verified machines
        # Due to escaping of cookie values we have a little workaround here
        # By default the cookie jar would generate the following header
        #   DES5c148...=HSARM.......xaA/O69Ws/CHfQ==SRVT
        # However we need the following
        #   DES5c148...="HSARM.......xaA/O69Ws/CHfQ==SRVT"
        # There is no way to get the cookie jar value with " around the value
        # so we manually modify the cookie (only this one) to be properly escaped  # noqa
        cookies = self.session.cookies
        for cookie in cookies:
            if cookie.name.startswith('DES') and '"' not in cookie.value:
                cookie.value = f'"{cookie.value}"'
                break

        resp = self.session.post(
            'https://idmsa.apple.com/appleauth/auth/signin',
            json={
                'accountName': self.username,
                'password': self.password,
                'rememberMe': True,
            },
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'X-Apple-Widget-Key': self.auth_service_key,
                'Accept': 'application/json, text/javascript',
            },
            cookies=cookies,
        )

        if resp.status_code in (401, 403):
            raise error.InvalidAuthCredential(
                f'Invalid username and password combination: {self.username}'
            )

        if not resp.ok and resp.status_code != 409:
            raise error.UnwantedResponse(f'{resp}: {resp.text}')
        return resp

    def handle_two_step_or_factor(self, resp):
        x_id = resp.headers['X-Apple-Id-Session-Id']
        scnt = resp.headers['scnt']
        logger.info(
            f'handle_two_step_or_factor, '
            f'username: {self.username}, x_id: {x_id}, scnt: {scnt}'
        )
        # get authentication options
        options_resp = self.session.get(
            'https://idmsa.apple.com/appleauth/auth',
            headers={
                'X-Apple-Id-Session-Id': x_id,
                'scnt': scnt,
                'X-Apple-Widget-Key': self.auth_service_key,
                'Accept': 'application/json',
            },
        )
        if not options_resp.ok:
            raise error.UnwantedResponse(
                f'{options_resp}: {options_resp.text}'
            )

        options_resp.encoding = 'utf-8'
        data = options_resp.json()
        # applied only handle two factor now
        if 'trustedPhoneNumbers' in data:
            self.two_factor_callback(
                self,
                x_id,
                scnt,
                {'backend_data': self.backend.backend_data, 'auth_data': data},
            )
        else:
            raise error.UnknownAuthOption(data)

    def two_factor_callback(self, portal, x_id, scnt, ctx) -> str:
        '''Notify waiting for two factor code

        this callback is called when session expired and
        need to handle two factor verification

        args is two factor request relative data
        callback need to handle smscode and call verify_smscode to continue
        '''
        # verify_smscode may be called outside, store session for outside usage
        self.store_session()
        self._two_factor_callback(portal, x_id, scnt, ctx)

    def verify_smscode(self, code, x_id, scnt):
        logger.info(
            f'verify_smscode, username: {self.username}, '
            f'x_id: {x_id}, scnt: {scnt}, code: {code}'
        )
        if not code:
            raise error.UnwantedResponse(f'{code}')
        if isinstance(code, bytes):
            code = code.decode()

        resp = self.session.post(
            'https://idmsa.apple.com/appleauth/auth/verify/trusteddevice/securitycode',  # noqa
            json={'securityCode': {'code': code}},
            headers={
                'X-Apple-Id-Session-Id': x_id,
                'scnt': scnt,
                'X-Apple-Widget-Key': self.auth_service_key,
                'Accept': 'application/json',
            },
        )
        if not resp.ok:
            raise error.UnwantedResponse(f'{resp}: {resp.text}')

        self.trust_device(x_id, scnt)
        self.store_session()

    def trust_device(self, x_id, scnt):
        # just need cookies
        self.session.get(
            'https://idmsa.apple.com/appleauth/auth/2sv/trust',
            headers={
                'X-Apple-Id-Session-Id': x_id,
                'scnt': scnt,
                'X-Apple-Widget-Key': self.auth_service_key,
            },
        )

    def renew_req(self, req):
        # req is PreparedRequest
        req.headers.pop('Cookie', '')
        req.prepare_cookies(merge_cookies(req._cookies, self.session.cookies))
        return req
