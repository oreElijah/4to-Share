from pydantic import BaseModel, EmailStr
from fastapi import Form
from typing import Optional
import uuid
from datetime import datetime

class LoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str

class LoginRequestSchema(BaseModel):
    email: EmailStr
    password: str



class TokenUser(BaseModel):
    id: str
    email: str

class TokenData(BaseModel):
    user: TokenUser
    exp: int
    jti: str
    refresh: bool = False