from dataclasses import dataclass, asdict

from applied.error import DuplicatedModel
from applied.error import UnknownModelData, UnknownModelType


def delegate(model, client):
    return type(
        model.__name__,
        (model,),
        {'client': client, 'delegated': True, '_cache': []}
    )


class ModelMeta(type):

    def __new__(cls, name, bases, attrs):
        model = type.__new__(cls, name, bases, attrs)
        if model.TYPE is not None:
            if (model.TYPE in model.MODEL_CLASSES and
                    not getattr(model, 'delegated', False)):
                raise DuplicatedModel(model.TYPE, model.MODEL_CLASSES)
            model.MODEL_CLASSES[model.TYPE] = model
        return model


@dataclass
class BaseModel(metaclass=ModelMeta):

    id: str

    TYPE = None
    MODEL_CLASSES = {}
    FILTER_FIELDS = set()
    INCLUDE_FIELDS = set()

    @classmethod
    def create(cls, **kwargs):
        '''Create model instance

        :kwargs: will be passed to build_create_data for validation
        '''
        data = cls.build_create_data(**kwargs)
        resp = cls.client.api_session.post(f'/{cls.TYPE}', json={'data': data})
        return cls.from_json(resp.json())

    @classmethod
    def get(cls, pk, include=()):
        params = {}
        if include and cls.INCLUDE_FIELDS:
            params['include'] = ','.join(set(include) & cls.INCLUDE_FIELDS)
        resp = cls.client.api_session.get(f'/{cls.TYPE}/{pk}', params=params)
        return cls.from_json(resp.json())

    @classmethod
    def all(cls, include=()):
        params = {}
        if include and cls.INCLUDE_FIELDS:
            params['include'] = ','.join(set(include) & cls.INCLUDE_FIELDS)
        resp = cls.client.api_session.get(f'/{cls.TYPE}', params=params)
        return cls.from_json(resp.json())

    @classmethod
    def find(cls, *, include=(), **query):
        if not cls._cache:
            cls._cache = cls.all(include)
        fields = cls.__dataclass_fields__
        # if no query data, will return the first instance
        for ins in cls._cache:
            if all(key in fields and getattr(ins, key) == value
                   for key, value in query.items()):
                return ins

    def update(self, **kwargs):
        update_data = self.build_update_data(**kwargs)
        resp = self.client.api_session.patch(
            f'/{self.TYPE}/{self.id}', json=update_data,
        )
        json_data = resp.json()
        data = json_data['data']
        self.update_attributes(self.filter_attributes(data['attributes']))
        self.update_relationships(
            data.get('relationships', {}), json_data.get('included', [])
        )
        return self

    def delete(self) -> bool:
        resp = self.client.api_session.delete(f'/{self.TYPE}/{self.id}')
        return resp.ok and resp.status_code == 204

    @classmethod
    def from_json(cls, json_data):
        # TODO: what to do with unknown fields?
        data = json_data['data']
        included = json_data.get('included', [])

        if isinstance(data, dict):
            return cls.to_model(data, included)
        elif isinstance(data, list):
            return [cls.to_model(ele, included) for ele in data]
        else:
            raise UnknownModelData(data)

    @classmethod
    def to_model(cls, data, included):
        model = cls.client.MODEL_CLASSES.get(data['type'])
        if not model:
            raise UnknownModelType(data['type'])
        values = {'id': data['id']}
        values.update(model.filter_attributes(data.get('attributes', {})))
        ins = model(**values)
        ins.update_relationships(data.get('relationships', {}), included)
        return ins

    @classmethod
    def filter_attributes(cls, attributes):
        values = {}
        for name, field in cls.__dataclass_fields__.items():
            if name == 'id':
                continue
            source = field.metadata.get('source', name)
            try:
                value = attributes[source]
            except KeyError:
                try:
                    value = attributes[name]
                except KeyError:
                    continue
            values[name] = value
        return values

    @classmethod
    def map_included(cls, relation, included):
        data = {}
        rid, rtype = relation['id'], relation['type']
        for include in included:
            if include['id'] == rid and include['type'] == rtype:
                data = include
                break
        if data:
            return cls.to_model(data, included)

    def update_relationships(self, relationships, included):
        attributes = {}
        map_included = self.map_included
        for key, value in relationships.items():
            data = value.get('data')
            if not data:
                continue
            if isinstance(data, dict):
                attributes[key] = map_included(data, included)
            elif isinstance(data, list):
                attributes[key] = [map_included(ele, included) for ele in data]
        self.update_attributes(self.filter_attributes(attributes))
        return self

    @classmethod
    def get_csrf_data(cls):
        session = cls.client.portal_session
        csrf = session.csrf_data.get(cls, {})
        if not csrf:
            csrf = cls.fetch_csrf_data()
        return csrf

    def update_attributes(self, attributes):
        fields = self.__class__.__dataclass_fields__
        for name, value in attributes.items():
            if name in fields:
                setattr(self, name, value)

    def as_dict(self):
        return asdict(self)
