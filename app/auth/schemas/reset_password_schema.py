from pydantic import BaseModel

class ResetPasswordRequestSchema(BaseModel):
    new_password: str