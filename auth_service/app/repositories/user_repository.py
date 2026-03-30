from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import User
from typing import Optional

class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def find_by_username(self, username: str) -> Optional[dict]:
        return await self.collection.find_one({"username": username})

    async def create_user(self, user: User) -> bool:
        result = await self.collection.insert_one(user.model_dump())
        return result.inserted_id is not None

    async def username_exists(self, username: str) -> bool:
        user = await self.find_by_username(username)
        return user is not None