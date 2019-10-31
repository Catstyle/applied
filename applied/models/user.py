from dataclasses import dataclass, field
from enum import Enum
from typing import List

from .base import BaseModel


@dataclass
class User(BaseModel):

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

    first_name: str = field(metadata={'source': 'firstName'})
    last_name: str = field(metadata={'source': 'lastName'})
    roles: List[str]
    provisioning_allowed: bool = field(
        metadata={'source': 'provisioningAllowed'}
    )
    allAppsVisible: bool = field(metadata={'source': 'allAppsVisible'})
    username: str

    TYPE = 'users'
    INCLUDE_FIELDS = {'visibleApps'}
