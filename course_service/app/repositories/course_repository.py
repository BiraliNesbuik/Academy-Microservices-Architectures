from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.course import Course, Purchase
from bson import ObjectId

class CourseRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["courses"]
        self.purchases = db["purchases"]

    async def create_course(self, course: Course):
        result = await self.collection.insert_one(course.model_dump())
        return str(result.inserted_id)

    async def get_all_courses(self):
        cursor = self.collection.find()
        courses = []
        async for document in cursor:
            document["id"] = str(document["_id"])
            courses.append(document)
        return courses

    async def get_course_by_id(self, course_id: str):
        document = await self.collection.find_one({"_id": ObjectId(course_id)})
        if document:
            document["id"] = str(document["_id"])
        return document

    async def purchase_course(self, purchase: Purchase):
        result = await self.purchases.insert_one(purchase.model_dump())
        return str(result.inserted_id)

    async def get_purchases_by_username(self, username: str):
        cursor = self.purchases.find({"username": username})
        purchases = []
        async for document in cursor:
            document["id"] = str(document["_id"])
            del document["_id"]
            purchases.append(document)
        return purchases

    async def update_course(self, course_id: str, data: dict):
        result = await self.collection.update_one(
            {"_id": ObjectId(course_id)},
            {"$set": data}
        )
        return result.modified_count > 0