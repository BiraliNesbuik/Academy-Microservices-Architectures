from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import User
from typing import Optional

class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def find_by_username(self, username: str) -> Optional[dict]:
        return await self.collection.find_one({"username": username}, {"_id": 0})

    async def create_user(self, user: User) -> bool:
        result = await self.collection.insert_one(user.model_dump())
        return result.inserted_id is not None

    async def username_exists(self, username: str) -> bool:
        user = await self.find_by_username(username)
        return user is not None

    async def get_all_users(self):
        cursor = self.collection.find({}, {"_id": 0, "hashed_password": 0})
        users = []
        async for user in cursor:
            users.append(user)
        return users

    async def update_user(self, username: str, data: dict) -> bool:
        result = await self.collection.update_one(
            {"username": username},
            {"$set": data}
        )
        return result.modified_count > 0

    async def delete_user(self, username: str) -> bool:
        result = await self.collection.delete_one({"username": username})
        return result.deleted_count > 0