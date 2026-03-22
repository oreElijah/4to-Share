from fastapi import Depends, status, BackgroundTasks, UploadFile, File, Form, Response
from fastapi.exceptions import HTTPException
from app.post.service import PostService
from typing import Annotated
from app.common.utils.router import VersionRouter
from app.common.utils.response import HTTPResponse
from app.post.schemas.post_request_schema import PostRequestSchema
from app.post.schemas.post_response_shcema import PostResponseSchema, FeedResponseSchema
from app.common.utils.dependencies import get_current_user
from app.database.model import User

post_router = VersionRouter(
    version="1",
    path="post",
    tags=["post"]
)

@post_router.post("/create_post", response_model=HTTPResponse[PostResponseSchema], status_code=status.HTTP_201_CREATED)
async def create_post(post_service: Annotated[PostService, Depends(PostService)],
                        file: UploadFile = File(...),
                        caption: str = Form(""),
                        user: User = Depends(get_current_user)):
    post = await post_service.upload_file(file, str(user.id), caption)
    return HTTPResponse(
        message="Post created successfully",
        data=post,
        status_code=status.HTTP_201_CREATED
    )

@post_router.get("/feed", response_model=HTTPResponse[FeedResponseSchema])
async def get_feed(post_service: Annotated[PostService, Depends(PostService)],
                    user: User = Depends(get_current_user)):
    
    feed = await post_service.get_feed(str(user.id))
    return HTTPResponse(
        message="Feed retrieved successfully",
        data=feed,
        status_code=status.HTTP_200_OK
    )

@post_router.delete("/delete/{post_id}", response_model=HTTPResponse[None])
async def delete_post(post_service: Annotated[PostService, Depends(PostService)],
                       post_id: str,
                       user: User = Depends(get_current_user)):
    await post_service.delete_post(post_id, str(user.id))
    return HTTPResponse(
        message="Post deleted successfully",
        data=None,
        status_code=status.HTTP_200_OK
    )

@post_router.get("/download/{post_id}")
async def download_post(post_service: Annotated[PostService, Depends(PostService)],
                        post_id: str):
    download_payload = await post_service.download_post(post_id)
    safe_filename = str(download_payload["filename"] or "download.bin").replace('"', "")
    return Response(
        content=download_payload["content"],
        media_type=str(download_payload["file_type"]),
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )
