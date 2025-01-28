from uuid import UUID

from amt.models import User as UserModel
from amt.schema.shared import BaseModel

type UserSchema = User


class User(BaseModel):
    id: UUID | None = None
    name: str | None = None
    email_hash: str | None = None
    name_encoded: str | None = None
    email: str | None = None

    @staticmethod
    def create_from_model(user_model: UserModel | None) -> UserSchema | None:
        if user_model is None:
            return None
        user_schema = User()
        user_schema.id = user_model.id
        user_schema.name = user_model.name
        user_schema.email_hash = user_model.email_hash
        user_schema.name_encoded = user_model.name_encoded
        user_schema.email = user_model.email
        return user_schema
