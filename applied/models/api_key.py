from base64 import b64decode
from dataclasses import dataclass, field
from enum import Enum
from typing import List

from applied import error

from .base import BaseModel
from .provider import Provider
from .queryset import Query, Result
from .user import User


@dataclass
class ApiKey(BaseModel):

    all_apps_visible: bool = field(metadata={'source': 'allAppsVisible'})
    can_download: bool = field(metadata={'source': 'canDownload'})
    is_active: bool = field(metadata={'source': 'isActive'})
    key_type: str = field(metadata={'source': 'keyType'})
    last_used: str = field(metadata={'source': 'lastUsed'})
    nickname: str
    private_key: str = field(metadata={'source': 'privateKey'})
    revoking_date: str = field(metadata={'source': 'revokingDate'})
    roles: List[str]

    created_by: User = field(
        init=False, default=None, metadata={'source': 'createdBy'},
    )
    provider: Provider = field(init=False, default=None)
    revoked_by: User = field(
        init=False, default=None, metadata={'source': 'revokedBy'},
    )

    TYPE = 'apiKeys'

    ONLY_FIELDS = {'apiKeys'}
    INCLUDE_FIELDS = {'createdBy', 'revokedBy', 'provider'}

    class Role(Enum):

        ADMIN = 'ADMIN'
        APP_MANAGER = 'APP_MANAGER'

    @classmethod
    def build_create_data(cls, nickname: str, roles: List[str]) -> dict:
        return {
            'type': cls.TYPE,
            'attributes': {
                'nickname': nickname,
                'roles': roles,
                'keyType': 'PUBLIC_API',
                'allAppsVisible': True,
            },
        }

    @classmethod
    def create(cls, **kwargs):
        '''Create model instance

        :kwargs: will be passed to build_create_data for validation
        '''
        data = cls.build_create_data(**kwargs)
        portal = cls.client.portal_session
        resp = portal.post(
            f'{portal.APC_IRIS_V1}/{cls.TYPE}', json={'data': data}
        )
        return cls.from_json(resp.json())

    @classmethod
    def get(cls, pk, *, includes=()):
        q = Query(includes=includes)
        params = q.get_params(cls)
        portal = cls.client.portal_session
        resp = portal.get(
            f'{portal.APC_IRIS_V1}/{cls.TYPE}/{pk}', params=params,
        )
        return cls.from_json(resp.json())

    @classmethod
    def find(cls, *, includes=()):
        q = Query(includes=includes)
        params = q.get_params(cls)
        portal = cls.client.portal_session
        resp = portal.get(f'{portal.APC_IRIS_V1}/{cls.TYPE}', params=params)
        return Result(cls, params, resp.json())

    def download_private_key(self):
        portal = self.client.portal_session
        resp = portal.session.get(
            f'{portal.APC_IRIS_V1}/apiKeys/{self.id}',
            params={'fields[apiKeys]': 'privateKey', 'include': 'provider'},
        )
        if resp.ok:
            data = resp.json()
            self.private_key = b64decode(
                data['data']['attributes']['privateKey']
            ).decode()
            self.provider = data['included'][0]['id']
            return self.private_key
        if resp.status_code == 410:
            raise error.ResourceNotFound(
                'private key can only be downloaded one time'
            )
        raise error.UnwantedResponse(f'{resp}: {resp.text}')
