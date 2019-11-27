from dataclasses import dataclass, asdict, MISSING

from applied import error

from .queryset import Query, Result


def delegate(model, client):
    return type(
        model.__name__, (model,), {'client': client, 'delegated': True},
    )


@dataclass
class BaseModel:

    id: str

    TYPE = None

    FILTER_FIELDS = set()
    ONLY_FIELDS = set()
    INCLUDE_FIELDS = set()
    SORT_FIELDS = set()
    RELATED_LIMIT = {}

    @classmethod
    def create(cls, **kwargs):
        '''Create model instance

        :kwargs: will be passed to build_create_data for validation
        '''
        data = cls.build_create_data(**kwargs)
        resp = cls.client.api_session.post(f'/{cls.TYPE}', json={'data': data})
        return cls.from_json(resp.json())

    @classmethod
    def get(cls, pk, *, includes=()):
        q = Query(includes=includes)
        params = q.get_params(cls)
        resp = cls.client.api_session.get(f'/{cls.TYPE}/{pk}', params=params)
        return cls.from_json(resp.json())

    @classmethod
    def find(
        cls,
        *,
        filters={},
        fields={},
        includes=(),
        sorts=(),
        limit=20,
        related_limits={},
    ):
        q = Query(
            filters=filters,
            fields=fields,
            includes=includes,
            sorts=sorts,
            limit=limit,
            related_limits=related_limits,
        )
        params = q.get_params(cls)
        resp = cls.client.api_session.get(f'/{cls.TYPE}', params=params)
        return Result(cls, params, resp.json())

    @classmethod
    def count(cls):
        # we only need the total in response meta
        # e.g.: ...'meta': {'total': 74, 'limit': 1}...
        return cls.find(limit=1).count

    def update(self, **kwargs):
        update_data = self.build_update_data(**kwargs)
        resp = self.client.api_session.patch(
            f'/{self.TYPE}/{self.id}', json=update_data,
        )
        json_data = resp.json()
        data = json_data['data']
        self.update_attributes(
            self.filter_attributes(data['attributes'], False)
        )
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
            raise error.UnknownModelData(data)

    @classmethod
    def to_model(cls, data, included):
        model = cls.client.MODEL_CLASSES.get(data['type'])
        if not model:
            raise error.UnknownModelType(data['type'])
        values = {'id': data['id']}
        values.update(model.filter_attributes(data.get('attributes', {})))
        ins = model(**values)
        ins.update_relationships(data.get('relationships', {}), included)
        return ins

    @classmethod
    def filter_attributes(cls, attributes, fill_missing=True):
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
                    if not fill_missing or not field.init:
                        continue
                    if field.default_factory is not MISSING:
                        value = field.default_factory()
                    elif field.default is not MISSING:
                        value = field.default
                    else:
                        value = field.type()
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
        self.update_attributes(self.filter_attributes(attributes, False))
        return self

    def update_attributes(self, attributes):
        fields = self.__class__.__dataclass_fields__
        for name, value in attributes.items():
            if name in fields:
                setattr(self, name, value)

    def as_dict(self):
        return asdict(self)
