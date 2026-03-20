from pydantic import BaseModel, EmailStr

class ForgotPasswordRequestSchema(BaseModel):
    email: EmailStr