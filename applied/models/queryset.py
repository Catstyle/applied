from collections import defaultdict

from applied import error, logger


class Query:

    MAX_LIMIT = 200
    RELATED_LIMIT = 50

    def __init__(
        self,
        *,
        filters: dict = {},
        fields: dict = {},
        includes: list = (),
        sorts: list = (),
        limit: int = 20,
        related_limits: dict = {},
    ):
        self.filters = defaultdict(list)
        self.fields = defaultdict(list)
        self.includes = set()
        self.sorts = []
        self.limit_count = 0
        self.related_limits = {}

        self.filter(**filters)
        self.only(**fields)
        self.include(*includes)
        self.sort(*sorts)
        self.limit(limit)
        self.limit_related(**related_limits)

    def filter(self, **filters):
        for attr, value in filters.items():
            if isinstance(value, (list, tuple)):
                self.filters[attr].extend(value)
            else:
                self.filters[attr].append(value)

    def only(self, **fields):
        for attr, value in fields.items():
            if isinstance(value, (list, tuple)):
                self.fields[attr].extend(value)
            else:
                self.fields[attr].append(value)

    def include(self, *includes):
        self.includes.update(includes)

    def sort(self, *sorts):
        for attr in sorts:
            if attr not in self.sorts:
                self.sorts.append(attr)

    def limit(self, limit):
        self.limit_count = max(min(limit, self.MAX_LIMIT), 1)

    def limit_related(self, **limits):
        for name, value in limits.items():
            self.related_limits[name] = max(min(value, self.RELATED_LIMIT), 1)

    def validate(self, model):
        unknown_filters = self.filters.keys() - model.FILTER_FIELDS
        if unknown_filters:
            raise error.UnknownModelFilter(
                model.FILTER_FIELDS, unknown_filters
            )

        unknown_fields = self.fields.keys() - model.ONLY_FIELDS
        if unknown_fields:
            raise error.UnknownModelField(model.ONLY_FIELDS, unknown_fields)

        unknown_includes = self.includes - model.INCLUDE_FIELDS
        if unknown_includes:
            raise error.UnknownModelInclude(
                model.INCLUDE_FIELDS, unknown_includes
            )

        unknown_sorts = set(self.sorts) - model.SORT_FIELDS
        if unknown_sorts:
            raise error.UnknownModelSort(model.SORT_FIELDS, unknown_sorts)

        unknown_limits = (
            self.related_limits.keys() - model.RELATED_LIMIT.keys()
        )
        if unknown_limits:
            raise error.UnknownModelLimits(model.RELATED_LIMIT, unknown_limits)

    def get_params(self, model):
        self.validate(model)

        params = {'limit': self.limit_count}
        for name, values in self.filters.items():
            params[f'filter[{name}]'] = ','.join(values)
        for name, values in self.fields.items():
            params[f'fields[{name}]'] = ','.join(values)
        if self.includes:
            params['include'] = ','.join(self.includes)
        if self.sorts:
            params['sort'] = ','.join(self.sorts)
        for name, values in self.related_limits.items():
            params[f'limit[{name}]'] = ','.join(values)

        logger.debug(
            f'get_params, filters: {self.filters}, fields: {self.fields}, '
            f'include: {self.includes}, sort: {self.sorts}, '
            f'limit: {self.limit}, related_limits: {self.related_limits}, '
            f'params: {params}'
        )

        return params


class Result:
    ''' query result helper container '''

    def __init__(self, model, params, data):
        self.model = model
        self.params = params
        self.objects = []
        self.load_objects(data)

    def load_objects(self, data):
        self.links = data['links']
        self.meta = data.get('meta', {})
        self.objects.extend(self.model.from_json(data))

    @property
    def count(self):
        if self.meta:
            return self.meta['paging']['total']
        return 0

    def rewind(self):
        if 'first' in self.links:
            self.objects = []
            resp = self.model.client.api_session.get(self.links['first'])
            self.load_objects(resp.json())

    def __iter__(self):
        pos = 0
        while 1:
            while pos < len(self.objects):
                yield self.objects[pos]
                pos += 1

            if 'next' not in self.links:
                return

            resp = self.model.client.api_session.get(self.links['next'])
            self.load_objects(resp.json())
