from .error import DuplicatedModel
from .interface import PortalSession, ApiSession
from .models import models
from .models.base import delegate


class Client:
    def __init__(
        self,
        portal_session: PortalSession = None,
        api_session: ApiSession = None,
    ):
        self.portal_session = portal_session
        self.api_session = api_session
        self.MODEL_CLASSES = {}

        for model in models.values():
            self.delegate(model)

    def delegate(self, model):
        if model.TYPE in self.MODEL_CLASSES:
            raise DuplicatedModel(model.TYPE)
        delegated = delegate(model, self)
        setattr(self, model.__name__, delegated)
        self.MODEL_CLASSES[model.TYPE] = delegated
