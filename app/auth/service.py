from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, HTTPException, status, Request
from datetime import timedelta
from typing import Annotated
from app.database.model import User
from app.mail.service import MailService
from app.user.service import UserService
from app.database.main import get_session
from settings.config import Configs, get_config 
from app.common.utils.utils import generate_password_hash, verify_password
from app.common.utils.utils import create_access_token, create_url_safe_token
from app.auth.schemas.forgot_password_schema import ForgotPasswordRequestSchema
from app.auth.schemas.login_schema import LoginRequestSchema, LoginResponseSchema
from app.auth.schemas.register_schema import RegisterRequestSchema, RegisterResponseSchema
from app.common.utils.response import HTTPResponse
class AuthService:
    def __init__(self,
                 config: Annotated[Configs, Depends(get_config)],
                session: AsyncSession= Depends(get_session)):
        self.session = session
        self.config = config
    
    async def login(self, login_data: LoginRequestSchema, user_service: Annotated[UserService, Depends(UserService)], request: Request | None = None) -> LoginResponseSchema:
        email = login_data.email
        
        user = await user_service.get_user_by_email(email=email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        password = login_data.password
        hashed_password = user.password

        IP_address = await user_service.get_IP_info(request) # type: ignore

        if user.IP_address != str(IP_address):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login attempt from unrecognized IP address"
            )

        password_valid = verify_password(plain_password=password, hashed_password=hashed_password)
        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        access_token = create_access_token(
            user_data={
                "id": str(user.id),
                "email": user.email
                }
                )
        
        refresh_token = create_access_token(
            user_data={
                "id": str(user.id),
                "email": user.email
                },
            refresh=True,
            expiry_time=timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS)
                )
        
        return LoginResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token)

        
    async def register(self, register_data: RegisterRequestSchema, mail_service: Annotated[MailService, Depends(MailService)], user_service: Annotated[UserService, Depends(UserService)], request: Request | None = None) -> RegisterResponseSchema:
        user_exists = await user_service.user_exists(email= register_data.email)

        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        user= await user_service.create_user(user_data=register_data, request=request) # type: ignore
        
        return RegisterResponseSchema(
            id=user.id,
            username=user.username,
            email=user.email,
            firstname=user.firstname,
            lastname=user.lastname,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    async def forgot_password(self, forgot_password_data: ForgotPasswordRequestSchema, mail_service: Annotated[MailService, Depends(MailService)], user_service: Annotated[UserService, Depends(UserService)]) -> User:
        user = await user_service.get_user_by_email(email= forgot_password_data.email)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email does not exist"
            )

        return user