from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, HTTPException
from sqlmodel import select
from typing import Sequence
from app.database.model import User
from app.database.main import get_session
from app.user.schemas.user_schemas import UserCreateSchema, UserUpdateSchema
from app.common.utils.utils import generate_password_hash

class UserService:
    def __init__(self, session: AsyncSession= Depends(get_session)):
        self.session = session

    async def get_all_users(self) -> Sequence[User]:
        stmt = select(User)
        
        result = await self.session.exec(stmt)
        
        return result.all()

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)

        result = await self.session.exec(stmt)
        
        user = result.first()

        # if user is None:
        #     raise HTTPException(status_code=404, detail="User not found")
    
        return user
    
    async def get_user_by_id(self, id: str) -> User | None:
        stmt = select(User).where(User.id == id)

        result = await self.session.exec(stmt)
        
        user = result.first()

        # if user is None:
        #     raise HTTPException(status_code=404, detail="User not found")
    
        return user

    async def user_exists(self, email: str) -> bool:
        user = await self.get_user_by_email(email)
        return user is not None
    
    async def create_user(self, user_data: UserCreateSchema) -> User:
        user_data_dict = user_data.model_dump()

        password = str(user_data_dict.get("password"))
     
        hashed_password = generate_password_hash(password)
     
        user_data_dict["password"] = hashed_password
        user = User(**user_data_dict)

        # user.password = generate_password_hash(str(user_data_dict["password"]))

        self.session.add(user)

        await self.session.commit()

        return user
    
    async def update_user(self, user: User, user_data: dict) -> User:

        # update_dict = user_data.model_dump(exclude_unset=True)

        for key, value in user_data.items():
            setattr(user, key, value)

        self.session.add(user)
        
        await self.session.commit()
        
        return user
    
    async def delete_user(self, user: User):
        await self.session.delete(user)
        await self.session.commit()