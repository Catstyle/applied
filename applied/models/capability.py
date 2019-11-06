from dataclasses import dataclass, field
from enum import Enum
from typing import List

from .base import BaseModel


@dataclass
class CapabilityOption:

    key: str
    name: str
    description: str
    enabled: bool
    enabled_by_default: bool = field(metadata={'source': 'enabledByDefault'})
    supports_wildcard: bool = field(metadata={'source': 'supportsWildcard'})


@dataclass
class CapabilitySetting:

    allowed_instances: str = field(metadata={'source': 'allowedInstances'})
    description: str
    key: str
    name: str
    visible: bool
    options: List[CapabilityOption]
    enabled_by_default: bool = field(metadata={'source': 'enabledByDefault'})
    min_instances: int = field(metadata={'source': 'minInstances'})


@dataclass
class Capability(BaseModel):

    capability_type: str = field(metadata={'source': 'capabilityType'})
    settings: List[CapabilitySetting]

    class Type(Enum):

        ICLOUD = 'ICLOUD'
        IN_APP_PURCHASE = 'IN_APP_PURCHASE'
        GAME_CENTER = 'GAME_CENTER'
        PUSH_NOTIFICATIONS = 'PUSH_NOTIFICATIONS'
        WALLET = 'WALLET'
        INTER_APP_AUDIO = 'INTER_APP_AUDIO'
        MAPS = 'MAPS'
        ASSOCIATED_DOMAINS = 'ASSOCIATED_DOMAINS'
        PERSONAL_VPN = 'PERSONAL_VPN'
        APP_GROUPS = 'APP_GROUPS'
        HEALTHKIT = 'HEALTHKIT'
        HOMEKIT = 'HOMEKIT'
        WIRELESS_ACCESSORY_CONFIGURATION = 'WIRELESS_ACCESSORY_CONFIGURATION'
        APPLE_PAY = 'APPLE_PAY'
        DATA_PROTECTION = 'DATA_PROTECTION'
        SIRIKIT = 'SIRIKIT'
        NETWORK_EXTENSIONS = 'NETWORK_EXTENSIONS'
        MULTIPATH = 'MULTIPATH'
        HOT_SPOT = 'HOT_SPOT'
        NFC_TAG_READING = 'NFC_TAG_READING'
        CLASSKIT = 'CLASSKIT'
        AUTOFILL_CREDENTIAL_PROVIDER = 'AUTOFILL_CREDENTIAL_PROVIDER'
        ACCESS_WIFI_INFORMATION = 'ACCESS_WIFI_INFORMATION'

    TYPE = 'bundleIdCapabilities'

    @classmethod
    def build_create_data(cls, capability_type: str, bundle_id: str,
                          settings: List[CapabilitySetting] = None) -> dict:
        return {
            'type': cls.TYPE,
            'attributes': {
                'capabilityType': capability_type,
                'settings': settings or [],
            },
            'relationships': {
                'bundleId': {'data': {'id': bundle_id, 'type': 'bundleIds'}},
            }
        }

    def build_update_data(self, capability_type: str,
                          settings: List[CapabilitySetting] = None) -> dict:
        return {
            'type': self.TYPE,
            'id': self.TYPE,
            'attributes': {
                'capabilityType': capability_type,
                'settings': settings or [],
            },
        }
