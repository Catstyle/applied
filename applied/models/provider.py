from dataclasses import dataclass, field

from .base import BaseModel
from .user import User


@dataclass
class Provider(BaseModel):

    name: str
    type: str
    status: str
    auto_renew: bool = field(metadata={'source': 'autoRenew'})
    organization_id: str = field(metadata={'source': 'organizationId'})

    users: User = field(
        init=False, default=None, metadata={'source': 'users'},
    )

    TYPE = 'contentProviders'
    INCLUDE_FIELDS = {'users'}
