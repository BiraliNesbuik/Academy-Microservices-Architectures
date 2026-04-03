from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.course import Course, Purchase, CartItem
from bson import ObjectId

class CourseRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["courses"]
        self.purchases = db["purchases"]
        self.db = db

    async def create_course(self, course: Course):
        result = await self.collection.insert_one(course.model_dump())
        return str(result.inserted_id)

    async def get_all_courses(self):
        cursor = self.collection.find({})
        courses = []
        async for document in cursor:
            document["id"] = str(document["_id"])
            del document["_id"]
            courses.append(document)
        return courses

    async def get_course_by_id(self, course_id: str):
        document = await self.collection.find_one(
            {"_id": ObjectId(course_id)},
            {"_id": 0}
        )
        return document

    async def purchase_course(self, purchase: Purchase):
        result = await self.purchases.insert_one(purchase.model_dump())
        return str(result.inserted_id)

    async def get_purchases_by_username(self, username: str):
        cursor = self.purchases.find({"username": username}, {"_id": 0})
        purchases = []
        async for document in cursor:
            purchases.append(document)
        return purchases

    async def update_course(self, course_id: str, data: dict):
        result = await self.collection.update_one(
            {"_id": ObjectId(course_id)},
            {"$set": data}
        )
        return result.modified_count > 0

    async def delete_course(self, course_id: str):
        result = await self.collection.delete_one({"_id": ObjectId(course_id)})
        return result.deleted_count > 0

    async def add_to_cart(self, username: str, course_id: str):
        existing = await self.db["cart"].find_one({"username": username})
        if existing:
            if course_id in existing.get("items", []):
                return False
            await self.db["cart"].update_one(
                {"username": username},
                {"$push": {"items": course_id}}
            )
        else:
            await self.db["cart"].insert_one({"username": username, "items": [course_id]})
        return True

    async def get_cart(self, username: str):
        cart = await self.db["cart"].find_one({"username": username}, {"_id": 0})
        return cart or {"username": username, "items": []}

    async def remove_from_cart(self, username: str, course_id: str):
        result = await self.db["cart"].update_one(
            {"username": username},
            {"$pull": {"items": course_id}}
        )
        return result.modified_count > 0

    async def checkout_cart(self, username: str):
        cart = await self.get_cart(username)
        if not cart["items"]:
            return []

        purchased = []
        for course_id in cart["items"]:
            purchase = Purchase(username=username, course_id=course_id)
            await self.purchase_course(purchase)
            purchased.append(course_id)

        await self.db["cart"].update_one(
            {"username": username},
            {"$set": {"items": []}}
        )
        return purchased