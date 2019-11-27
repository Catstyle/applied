from dataclasses import dataclass, field

from .base import BaseModel


@dataclass
class Device(BaseModel):

    udid: str
    name: str
    device_class: str = field(metadata={'source': 'deviceClass'})
    model: str
    platform: str
    added_date: str = field(metadata={'source': 'addedDate'})
    status: str

    TYPE = 'devices'

    FILTER_FIELDS = {'id', 'name', 'udid', 'status', 'platform'}
    ONLY_FIELDS = {'devices'}
    SORT_FIELDS = {
        'id',
        '-id',
        'name',
        '-name',
        'platform',
        '-platform',
        'status',
        '-status',
        'udid',
        '-udid',
    }

    @classmethod
    def build_create_data(cls, udid: str, name: str, platform: str) -> dict:
        return {
            'type': cls.TYPE,
            'attributes': {'udid': udid, 'name': name, 'platform': platform},
        }

    def build_update_data(self, name: str = None, status: str = None):
        return {
            'type': self.TYPE,
            'id': self.id,
            'attributes': {
                'name': name or self.name,
                'status': status or self.status,
            },
        }
