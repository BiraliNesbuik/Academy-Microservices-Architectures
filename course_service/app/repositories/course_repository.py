from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.course import Course

class CourseRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["courses"]

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