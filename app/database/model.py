from sqlmodel import Relationship, SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
import uuid
from datetime import datetime

class Post(SQLModel, table=True):
    __tablename__ = "posts" # type: ignore

    id: uuid.UUID = Field(
         sa_column=Column(pg.UUID(),
                          primary_key=True,
                         default=uuid.uuid4,
                         unique=True,
                         index=True,
                         nullable=False))
    caption: str
    url: str
    file_type: str
    filename: str
    user_id: uuid.UUID = Field(foreign_key="users.id")
    user: "User" = Relationship(back_populates="posts")
    created_at: datetime = Field(
        sa_column=Column(
        pg.TIMESTAMP,
        nullable=False,
        default=datetime.now
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
        pg.TIMESTAMP,
        nullable=False,
        default=datetime.now
        )
    )


class User(SQLModel, table=True):
    __tablename__ = "users" # type: ignore
    id: uuid.UUID = Field(
         sa_column=Column(pg.UUID(),
                          primary_key=True,
                         default=uuid.uuid4,
                         unique=True,
                         index=True,
                         nullable=False))
    username: str
    email: str
    firstname: str
    lastname: str
    is_verified: bool = Field(default=False)
    posts: "Post" = Relationship(back_populates="user")
    created_at: datetime = Field(
        sa_column=Column(
        pg.TIMESTAMP,
        nullable=False,
        default=datetime.now
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
        pg.TIMESTAMP,
        nullable=False,
        default=datetime.now
        )
    )
    password: str

    def __repr__(self):
        return f"<User> {self.username}"