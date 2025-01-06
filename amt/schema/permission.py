from amt.core.authorization import AuthorizationVerb
from amt.schema.shared import BaseModel


class Permission(BaseModel):
    resource: str
    verb: list[AuthorizationVerb]
