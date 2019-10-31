from dataclasses import dataclass, field
from enum import Enum
from typing import List

from .base import BaseModel
from .bundle import BundleId
from .certificate import Certificate
from .device import Device


@dataclass
class Profile(BaseModel):

    uuid: str
    name: str
    platform: str
    profile_type: str = field(metadata={'source': 'profileType'})
    profile_content: str = field(metadata={'source': 'profileContent'})
    profile_state: str = field(metadata={'source': 'profileState'})
    created_date: str = field(metadata={'source': 'createdDate'})
    expiration_date: str = field(metadata={'source': 'expirationDate'})

    distribution_type: str = field(init=False, default='')
    bundle_id: BundleId = field(
        init=False, default=None, metadata={'source': 'bundleId'}
    )
    certificates: List[Certificate] = field(init=False, default_factory=list)
    devices: List[Device] = field(init=False, default_factory=list)

    TYPE = 'profiles'
    INCLUDE_FIELDS = {'bundleId', 'certificates', 'devices'}

    class Type(Enum):

        IOS_APP_DEVELOPMENT = 'IOS_APP_DEVELOPMENT'
        IOS_APP_STORE = 'IOS_APP_STORE'
        IOS_APP_ADHOC = 'IOS_APP_ADHOC'
        IOS_APP_INHOUSE = 'IOS_APP_INHOUSE'
        MAC_APP_DEVELOPMENT = 'MAC_APP_DEVELOPMENT'
        MAC_APP_STORE = 'MAC_APP_STORE'
        MAC_APP_DIRECT = 'MAC_APP_DIRECT'
        TVOS_APP_DEVELOPMENT = 'TVOS_APP_DEVELOPMENT'
        TVOS_APP_STORE = 'TVOS_APP_STORE'
        TVOS_APP_ADHOC = 'TVOS_APP_ADHOC'
        TVOS_APP_INHOUSE = 'TVOS_APP_INHOUSE'

    class State(Enum):

        ACTIVE = 'ACTIVE'
        INVALID = 'INVALID'

    TYPE_SYMBOLS = {
        'IOS_APP_ADHOC': 'adhoc',
        'IOS_APP_STORE': 'store',
    }

    def __post_init__(self):
        self.distribution_type = self.TYPE_SYMBOLS.get(
            self.profile_type, self.profile_type
        )

    @classmethod
    def fetch_csrf_data(cls):
        session = cls.client.portal_session
        resp = session.post(
            f'{session.DEV_QH65B2}/account/ios/profile/'
            'listProvisioningProfiles.action',
            data={
                'teamId': session.team_id,
                'pageNumber': 1,
                'pageSize': 1,
                'sort': 'name=asc',
            }
        )
        csrf_data = {
            'csrf': resp.headers.get('csrf', ''),
            'csrf_ts': resp.headers.get('csrf_ts', ''),
        }
        session.csrf_data[cls] = csrf_data
        return csrf_data

    @classmethod
    def build_create_data(cls, name, profile_type, bundle_id, certificates,
                          devices):
        return {
            'type': cls.TYPE,
            'attributes': {
                'name': name,
                'profileType': profile_type,
            },
            'relationships': {
                'bundleId': {'data': {'id': bundle_id, 'type': 'bundleIds'}},
                'certificates': {
                    'data': [
                        {'id': cid, 'type': 'certificates'}
                        for cid in certificates
                    ],
                },
                'devices': {
                    'data': [
                        {'id': did, 'type': 'devices'} for did in devices
                    ],
                }
            }
        }

    def build_update_data(self, name, app_id, certificates, devices):
        if not certificates:
            certificates = [cert.id for cert in self.certificates]
        if not devices:
            devices = [device.id for device in self.devices]
        return {
            'teamId': self.client.portal_session.team_id,
            'provisioningProfileId': self.id,
            'provisioningProfileName': name or self.name,
            'appIdId': app_id or self.bundle_id.id,
            'distributionType': self.distribution_type,
            'certificateIds': ','.join(certificates),
            'deviceIds': ','.join(devices),
        }

    def update(self, name: str = None, app_id: str = None,
               certificates: List[str] = None, devices: List[str] = None):
        ''' update a specified profile

        since app store connect api donot permit update
        we need to use developer.apple.com api, known as portal api
        so we need to use portal session explicitly
        '''
        csrf_data = self.get_csrf_data()
        data = self.build_update_data(name, app_id, certificates, devices)
        self.client.portal_session.post(
            f'{self.client.portal_session.DEV_QH65B2}/account/ios/profile'
            '/regenProvisioningProfile.action',
            data=data,
            headers=csrf_data,
        )
        # it is simpler just re-fetch profile from api
        del self._cache[:]
        return self.find(name=self.name)
