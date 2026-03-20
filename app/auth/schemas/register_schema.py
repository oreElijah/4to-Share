from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
import uuid

class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
    email: EmailStr
    firstname: str
    lastname: str
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

class RegisterRequestSchema(BaseModel):
    username: str
    email: EmailStr
    firstname: str
    lastname: str
    password: str



class RegisterResponseSchema(UserSchema):
   ...