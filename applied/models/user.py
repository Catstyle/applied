from dataclasses import dataclass, field
from enum import Enum
from typing import List

from .base import BaseModel


@dataclass
class VisibleApp:

    id: str
    type: str


@dataclass
class User(BaseModel):

    first_name: str = field(metadata={'source': 'firstName'})
    last_name: str = field(metadata={'source': 'lastName'})
    roles: List[str]
    provisioning_allowed: bool = field(
        metadata={'source': 'provisioningAllowed'}
    )
    allAppsVisible: bool = field(metadata={'source': 'allAppsVisible'})
    username: str

    visible_apps: VisibleApp = field(
        init=False, default_factory=list, metadata={'source': 'visibleApps'},
    )

    class Role(Enum):

        ADMIN = 'ADMIN'
        FINANCE = 'FINANCE'
        TECHNICAL = 'TECHNICAL'
        SALES = 'SALES'
        MARKETING = 'MARKETING'
        DEVELOPER = 'DEVELOPER'
        ACCOUNT_HOLDER = 'ACCOUNT_HOLDER'
        READ_ONLY = 'READ_ONLY'
        APP_MANAGER = 'APP_MANAGER'
        ACCESS_TO_REPORTS = 'ACCESS_TO_REPORTS'
        CUSTOMER_SUPPORT = 'CUSTOMER_SUPPORT'

    TYPE = 'users'

    FILTER_FIELDS = {'roles', 'visibleApps', 'username'}
    ONLY_FIELDS = {'apps', 'users'}
    INCLUDE_FIELDS = {'visibleApps'}
    SORT_FIELDS = {'lastName', '-lastName', 'username', '-username'}
    RELATED_LIMIT = {'visibleApps': 50}
