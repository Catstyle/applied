from dataclasses import dataclass, field
from enum import Enum
from typing import List

from .base import BaseModel


@dataclass
class BundleId(BaseModel):

    identifier: str
    name: str
    platform: str
    seed_id: str = field(metadata={'source': 'seedId'})

    profiles: List['Profile'] = field(init=False, default_factory=list)
    capabilities: List['Capability'] = field(
        init=False, default_factory=list,
        metadata={'source': 'bundleIdCapabilities'}
    )

    TYPE = 'bundleIds'
    INCLUDE_FIELDS = {'bundleIdCapabilities', 'profiles'}

    class Platform(Enum):

        IOS = 'IOS'
        MAC_OS = 'MAC_OS'

    @classmethod
    def build_create_data(cls, identifier: str, name: str, platform: str,
                          seed_id: str = None) -> dict:
        data = {
            'type': cls.TYPE,
            'attributes': {
                'identifier': identifier,
                'name': name,
                'platform': platform,
            },
        }
        if seed_id:
            data['attributes']['seedId'] = seed_id
        return data

    def build_update_data(self, name: str):
        return {
            'data': {
                'type': self.TYPE,
                'id': self.id,
                'attributes': {'name': name},
            }
        }
