from pydantic import BaseModel, RootModel

from amt.core.authorization import AuthorizationResource, AuthorizationVerb
from amt.schema.shared import BaseModel


class Permission(BaseModel):
    resource: AuthorizationResource
    verb: AuthorizationVerb
