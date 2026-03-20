from fastapi import Depends, status, BackgroundTasks, UploadFile, File
from fastapi.exceptions import HTTPException
from datetime import timedelta
from typing import List
# from settings.config import GlobalConfig as Config
from app.database.model import User
from app.user.service import UserService
from typing import Annotated
from app.redis.main import add_jti_to_blocklist
from app.common.utils.router import VersionRouter
from app.common.utils.response import HTTPResponse
from app.user.schemas.user_schemas import UserUpdateSchema
from app.user.schemas.user_response_schema import UserResponseSchema
from app.common.utils.dependencies import get_current_user, RoleChecker, AccessTokenBearer, RefreshTokenBearer
from app.common.utils.utils import create_access_token, create_url_safe_token, verify_password, generate_password_hash

user_router = VersionRouter(
    version="1",
    path="user",
    tags=["user"]
)


@user_router.get("/", response_model=HTTPResponse[List[UserResponseSchema]])
async def get_users(user_service: Annotated[UserService, Depends(UserService)], _: dict= Depends(AccessTokenBearer())):
    users = await user_service.get_all_users()

    if users is not None:
        return HTTPResponse(message="Users retrieved successfully", data=users, status_code=status.HTTP_200_OK)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
                         detail="Sorry, no users found")

@user_router.get("/users/{user_id}", response_model=HTTPResponse[UserResponseSchema])
async def get_user_by_id(user_id: str, user_service: Annotated[UserService, Depends(UserService)],  _: dict= Depends(AccessTokenBearer())):
    user = await user_service.get_user_by_id(user_id)

    if user is not None:
        return HTTPResponse(message="User retrieved successfully", data=user, status_code=status.HTTP_200_OK)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
                         detail="Sorry, no user found with this id")

@user_router.get("/profile/", response_model=HTTPResponse[UserResponseSchema])
async def get_current_user_profile(current_user = Depends(get_current_user), _: dict= Depends(AccessTokenBearer())):
    return HTTPResponse(
        message="User profile retrieved successfully",
        data=current_user,
        status_code=status.HTTP_200_OK
    )

@user_router.patch("/profile_update/", response_model=HTTPResponse[UserResponseSchema])
async def update_current_user_profile(user_service: Annotated[UserService, Depends(UserService)],
    user_update_model: UserUpdateSchema,
                                        current_user: User= Depends(get_current_user)):
    if current_user is not None:
        updated_user = await user_service.update_user(current_user, user_update_model.model_dump(exclude_unset=True))
    
        return HTTPResponse(
            message="User profile updated successfully",
            data=updated_user,
            status_code=status.HTTP_200_OK
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

@user_router.delete("/delete_account/", response_model=HTTPResponse[UserResponseSchema])
async def delete_current_user_account(user_service: Annotated[UserService, Depends(UserService)],
    current_user: User= Depends(get_current_user),
    token_data: dict= Depends(AccessTokenBearer())
    ):
    if current_user is not None:
        await user_service.delete_user(current_user)

        jti = str(token_data.get("jti"))
        await add_jti_to_blocklist(jti)

        return HTTPResponse(
            message="User account deleted successfully",
            data={},
            status_code=status.HTTP_200_OK
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )