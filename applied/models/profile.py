from dataclasses import dataclass, field
from enum import Enum
from typing import List

from .. import error

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

    TYPE = 'profiles'

    FILTER_FIELDS = {'id', 'name', 'profileState', 'profileType'}
    ONLY_FIELDS = {'certificates', 'devices', 'profiles', 'bundleIds'}
    INCLUDE_FIELDS = {'bundleId', 'certificates', 'devices'}
    SORT_FIELDS = {
        'id',
        '-id',
        'name',
        '-name',
        'profileState',
        '-profileState',
        'profileType',
        '-profileType',
    }
    RELATED_LIMIT = {'certificates': 50, 'devices': 50}

    def __post_init__(self):
        self.distribution_type = self.TYPE_SYMBOLS.get(
            self.profile_type, self.profile_type
        )

    def fetch_csrf_data(self):
        portal = self.client.portal_session
        resp = portal.post(
            f'{portal.DEV_QH65B2}/account/ios/profile/'
            'listProvisioningProfiles.action',
            data={
                'teamId': portal.team_id,
                'pageNumber': 1,
                'pageSize': 1,
                'sort': 'name=asc',
            },
            headers={'X-HTTP-Method-Override': 'GET'},
        )
        if not ('csrf' in resp.headers and 'csrf_ts' in resp.headers):
            raise error.NoCsrfData(self.__class__)
        return {
            'csrf': resp.headers['csrf'],
            'csrf_ts': resp.headers['csrf_ts'],
        }

    @classmethod
    def build_create_data(
        cls, name, profile_type, bundle_id, certificates, devices
    ):
        return {
            'type': cls.TYPE,
            'attributes': {'name': name, 'profileType': profile_type},
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
                },
            },
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

    def update(
        self,
        name: str = None,
        app_id: str = None,
        certificates: List[str] = None,
        devices: List[str] = None,
    ) -> 'Profile':
        ''' update a specified profile

        since app store connect api donot permit update
        we need to use developer.apple.com api, known as portal api
        so we need to use portal session explicitly
        '''
        data = self.build_update_data(name, app_id, certificates, devices)
        resp = self.client.portal_session.post(
            f'{self.client.portal_session.DEV_QH65B2}/account/ios/profile'
            '/regenProvisioningProfile.action',
            data=data,
            headers=self.fetch_csrf_data(),
        )
        # construct new instance
        json = resp.json()['provisioningProfile']
        data = {
            'id': json['provisioningProfileId'],
            'type': self.TYPE,
            'attributes': {
                'uuid': json['UUID'],
                'name': json['name'],
                'platform': json['proProPlatform'].upper(),
                'profile_type': json['type'].upper(),
                'profile_content': json['encodedProfile'],
                'profile_state': json['status'].upper(),
                'created_date': '',
                'expiration_date': json['dateExpire'],
            },
        }
        ins = self.to_model(data, [])
        ins.distribution_type = json['distributionType']
        return ins
