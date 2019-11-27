class AppliedError(Exception):
    ''' base exception for applied module '''


class InvalidRequest(AppliedError):
    ''' something wrong in request '''


class InvalidRequestData(AppliedError):
    ''' something wrong in request data '''


class NotAuthenticated(AppliedError):
    ''' session expired or not login '''


class PermissionDenied(AppliedError):
    ''' permission wrong '''


class MissingField(AppliedError):
    ''' field value not exist in resp data '''


class InvalidCreationData(AppliedError):
    ''' something wrong in creation request data '''


class MaxRetries(AppliedError):
    ''' something wrong when communicating with apple api server '''


class ResourceNotFound(AppliedError):
    ''' resource not found(404) '''


class InvalidAuthCredential(AppliedError):
    ''' invalid auth data '''


class UnknownAuthOption(AppliedError):
    ''' cannot handle auth option '''


class UnwantedResponse(AppliedError):
    ''' cannot handle auth option '''


class UnknownModelData(AppliedError):
    ''' cannot handle model data '''


class UnknownModelType(AppliedError):
    ''' cannot handle model type '''


class UnknownModelFilter(AppliedError):
    ''' model has no such filter '''


class UnknownModelField(AppliedError):
    ''' model has no such field '''


class UnknownModelInclude(AppliedError):
    ''' model has no such include '''


class UnknownModelSort(AppliedError):
    ''' model has no such sort '''


class UnknownModelLimits(AppliedError):
    ''' model has no such related limit '''


class DuplicatedModel(AppliedError):
    ''' check model type '''


class InvalidJWT(AppliedError):
    ''' cannot encode jwt '''


class NoCsrfData(AppliedError):
    ''' no csrf data found in resp headers '''
