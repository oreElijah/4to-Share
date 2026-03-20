from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid

class PostResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID 
    caption: str
    url: str
    file_type: str
    filename: str
    user_id: uuid.UUID 
    created_at: datetime 
    updated_at: datetime 


class FeedPostItemSchema(PostResponseSchema):
    is_owner: bool
    email: str


class FeedResponseSchema(BaseModel):
    post: list[FeedPostItemSchema]
    