from pydantic import BaseModel, EmailStr
from pydantic import ConfigDict
from datetime import datetime
import uuid


class UserResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
    email: EmailStr
    firstname: str
    lastname: str
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
