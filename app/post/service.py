from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Annotated, Sequence
import tempfile, shutil, os
import httpx
from fastapi import Depends, UploadFile, status
from fastapi.exceptions import HTTPException
from app.user.service import UserService
from settings.config import Configs, get_config
from app.database.main import get_session
from app.database.model import Post
from ..images.main import imagekit

class PostService:
    def __init__(self,
                 user_service: Annotated[UserService, Depends(UserService)],
                 setting: Annotated[Configs, Depends(get_config)],
                 session: AsyncSession= Depends(get_session)):
        self.user_service = user_service
        self.setting = setting
        self.session = session

    async def create_post(self, post: Post) -> Post:
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post
    
    async def get_post_by_id(self, post_id: str) -> Post:
        stmt = select(Post).where(Post.id == post_id)
        result = await self.session.exec(stmt)
        return result.first() # type: ignore
    
    async def get_all_posts(self) -> Sequence[Post]:
        stmt = select(Post).order_by(desc(Post.created_at))
        result = await self.session.exec(stmt)
        return result.all()

    async def get_feed(self, user_id: str):
        post_result = await self.get_all_posts()
        posts = list(post_result)  

        user_result = await self.user_service.get_all_users()
        users = list(user_result)  

        user_dict = {user.id: user.username for user in users}

        post_data = []
        for post in posts:
            post_data.append(
                {
                    "id": str(post.id),
                    "user_id": str(post.user_id),
                    "caption": post.caption,
                    "url": post.url,
                    "file_type": post.file_type,
                    "filename": post.filename,
                    "created_at": post.created_at.isoformat(),
                    "updated_at": post.updated_at.isoformat(),
                    "is_owner": str(post.user_id) == user_id,
                    "email": user_dict.get(post.user_id, "Unknown")
                }
            )
        return {"post":post_data}
    
    async def delete_post(self, post_id: str, user_id: str):
        post = await self.get_post_by_id(post_id=post_id)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        if str(post.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this post"
            )
        await self.session.delete(post)
        await self.session.commit()

    async def upload_file(self, file: UploadFile, user_id: str, caption: str):
        temp_file_path = None
        try:
            suffix = os.path.splitext(file.filename or "")[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file_path = temp_file.name
                shutil.copyfileobj(file.file, temp_file)

            # Re-open in a managed context so Windows can release the handle before cleanup.
            with open(temp_file_path, "rb") as upload_stream:
                upload_result = await imagekit.files.upload(
                    file=upload_stream,
                    file_name=file.filename, # type: ignore
                    use_unique_file_name=True,
                    tags=["backend-upload"]
                )

            if upload_result and hasattr(upload_result, 'url'):
                post = Post(
                    caption=caption,
                    url=upload_result.url,
                    file_type=file.content_type, # type: ignore
                    filename=file.filename, # type: ignore
                    user_id=user_id
                )
                created_post = await self.create_post(post)
                return created_post
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File upload failed: {str(e)}"
            )
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            file.file.close()

    async def download_post(self, post_id: str):
        post = await self.get_post_by_id(post_id=post_id)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=60.0,
                headers={"User-Agent": "PhotoSharingDownload/1.0"},
            ) as client:
                response = await client.get(post.url)
                response.raise_for_status()
        except httpx.HTTPError:
            return {
                "filename": post.filename,
                "file_type": post.file_type or "application/octet-stream",
                "content": None,
                "redirect_url": post.url,
            }

        return {
            "filename": post.filename,
            "file_type": response.headers.get("content-type") or post.file_type or "application/octet-stream",
            "content": response.content,
            "redirect_url": None,
        }
