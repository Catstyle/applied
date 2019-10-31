from dataclasses import dataclass, field

from .base import BaseModel


@dataclass
class App(BaseModel):

    bundle_id: str = field(metadata={'source': 'bundleId'})
    name: str
    sku: str
    primary_locale: str = field(metadata={'source': 'primaryLocale'})
    removed: str
    is_aag: str = field(metadata={'source': 'isAAG'})

    TYPE = 'apps'
