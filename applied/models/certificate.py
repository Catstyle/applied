from dataclasses import dataclass, field
from enum import Enum

from .base import BaseModel


@dataclass
class Certificate(BaseModel):

    serial_number: str = field(
        init=False, default='', metadata={'source': 'serialNumer'}
    )
    name: str
    display_name: str = field(metadata={'source': 'displayName'})
    platform: str
    expiration_date: str = field(metadata={'source': 'expirationDate'})
    certificate_type: str = field(metadata={'source': 'certificateType'})
    certificate_content: str = field(metadata={'source': 'certificateContent'})

    class Type(Enum):

        IOS_DEVELOPMENT = 'IOS_DEVELOPMENT'
        IOS_DISTRIBUTION = 'IOS_DISTRIBUTION'
        MAC_APP_DISTRIBUTION = 'MAC_APP_DISTRIBUTION'
        MAC_INSTALLER_DISTRIBUTION = 'MAC_INSTALLER_DISTRIBUTION'
        MAC_APP_DEVELOPMENT = 'MAC_APP_DEVELOPMENT'
        DEVELOPER_ID_KEXT = 'DEVELOPER_ID_KEXT'
        DEVELOPER_ID_APPLICATION = 'DEVELOPER_ID_APPLICATION'

    TYPE = 'certificates'

    FILTER_FIELDS = {
        'id',
        'certificateType',
        'displayName',
        'serialNumer',
        'seedId',
    }
    ONLY_FIELDS = {'certificates'}
    SORT_FIELDS = {
        'id',
        '-id',
        'displayName',
        '-displayName',
        'certificateType',
        '-certificateType',
        'serialNumer',
        '-serialNumer',
    }
    RELATED_LIMIT = {'profiles': 50}

    @classmethod
    def build_create_data(cls, certificate_type: str, csr: str) -> dict:
        return {
            'type': cls.TYPE,
            'attributes': {
                'certificateType': certificate_type,
                'csrContent': csr,
            },
        }
