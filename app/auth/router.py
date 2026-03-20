from fastapi import Depends, status, BackgroundTasks, UploadFile, File
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from app.auth.service import AuthService
from typing import Annotated
from app.user.service import UserService
from app.mail.service import MailService
from app.redis.main import add_jti_to_blocklist
from app.common.utils.router import VersionRouter
from app.common.utils.response import HTTPResponse
from app.auth.schemas.reset_password_schema import ResetPasswordRequestSchema
from app.auth.schemas.forgot_password_schema import ForgotPasswordRequestSchema
from app.auth.schemas.login_schema import LoginResponseSchema, LoginRequestSchema
from app.auth.schemas.register_schema import RegisterRequestSchema, RegisterResponseSchema
from app.common.utils.dependencies import get_current_user, RoleChecker, AccessTokenBearer, RefreshTokenBearer
from app.common.utils.utils import create_url_safe_token, decode_url_safe_token, generate_password_hash, create_access_token
from settings.config import Configs as Config

auth_router = VersionRouter(
    version="1",
    path="auth",
    tags=["auth"]
)

@auth_router.post("/register/", response_model=HTTPResponse[RegisterResponseSchema], status_code=status.HTTP_201_CREATED)
async def create_user(
                      register_schema: RegisterRequestSchema,
                      auth_service: Annotated[AuthService, Depends(AuthService)],
                      mail_service: Annotated[MailService, Depends(MailService)],
                      user_service: Annotated[UserService, Depends(UserService)],
                      background_tasks: BackgroundTasks,
                      ):
    user_response = await auth_service.register(register_schema, mail_service, user_service)

    token = create_url_safe_token({"email": register_schema.email}) # type: ignore
    background_tasks.add_task(mail_service.send_verify_mail, first_name=register_schema.firstname, email=register_schema.email, verify_token=token) # type: ignore

    return HTTPResponse(
            message="User registered successfully. Please check your email to verify your account.",
            data=user_response,
            status_code=status.HTTP_201_CREATED
        )
    
@auth_router.get("/verify/{token}", response_model=HTTPResponse[RegisterResponseSchema])
async def verify_email(user_service: Annotated[UserService, Depends(UserService)],token: str):
    token_data = decode_url_safe_token(token)

    email = str(token_data.get("email"))
    user = await user_service.get_user_by_email(email)

    await user_service.update_user(user, {"is_verified": True}) # type: ignore
    return {"message": "Email verified successfully", "data": user}

@auth_router.post("/login/", response_model=HTTPResponse[LoginResponseSchema])
async def login_user(auth_service: Annotated[AuthService, Depends(AuthService)], user_service: Annotated[UserService, Depends(UserService)], login_schema: LoginRequestSchema):
    result = await auth_service.login(login_schema, user_service)

    return HTTPResponse(
                message="Login successful",
                data=result,
                status_code=status.HTTP_200_OK
            )
    
@auth_router.post("/forgot_password/")
async def forgot_password(
                          model: ForgotPasswordRequestSchema,    
                          auth_service: Annotated[AuthService, Depends(AuthService)],
                          mail_service: Annotated[MailService, Depends(MailService)],
                          user_service: Annotated[UserService, Depends(UserService)],
                          background_tasks: BackgroundTasks,
                           ):
    user = await auth_service.forgot_password(model, mail_service, user_service)

    token = create_url_safe_token({"email": model.email})

    background_tasks.add_task(mail_service.send_password_reset,
                               first_name=user.firstname,
                                 email=user.email,
                                   token=token)

    return HTTPResponse(
            message="Check email to reset your password",
            data= user,
            status_code=status.HTTP_202_ACCEPTED
        )
    
@auth_router.post("/reset_password/{token}")
async def reset_password(user_service: Annotated[UserService, Depends(UserService)],token: str, model: ResetPasswordRequestSchema):
    token_data = decode_url_safe_token(token)

    email = str(token_data.get("email"))
    user = await user_service.get_user_by_email(email)
    if user is not None:
        hashed_password = generate_password_hash(model.new_password)
        await user_service.update_user(user, {"password": hashed_password})
        return HTTPResponse(
            message="Password reset successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid token or user does not exist"
    )


@auth_router.get("/reset_password/{token}")
async def redirect_reset_password(token: str):
    # Backward compatibility: old email links that point to API now redirect to Streamlit.
    return RedirectResponse(url=f"{Config.FRONTEND_URL}/?reset_token={token}")

@auth_router.get("/logout/")
async def logout_user(token_data: dict= Depends(AccessTokenBearer())):
    jti = str(token_data.get("jti"))
    await add_jti_to_blocklist(jti)

    return HTTPResponse(
        message="Logout successful",
        data=None,
        status_code=status.HTTP_200_OK
    )

@auth_router.post("/refresh/")
async def refresh_token(token_detail: dict= Depends(RefreshTokenBearer())):
    if token_detail.get("refresh"):
        user = token_detail.get("user")
        new_access_token = create_access_token(
            user_data={
                "id": user["id"], # type: ignore
                "email": user.get("email"), # type: ignore
                "role": user.get("role") # type: ignore
            }
        )
        return HTTPResponse(
            message="Access token refreshed successfully",
            data={"access_token": new_access_token},
            status_code=status.HTTP_200_OK
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token"
    )
