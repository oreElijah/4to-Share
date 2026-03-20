from pydantic import BaseModel
from datetime import datetime
import uuid

class PostRequestSchema(BaseModel):
    title: str
    caption: str
    