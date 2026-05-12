from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc)


def _out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


class BookingRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.appointments = db["appointments"]

    async def create_appointment(self, data: dict) -> dict:
        now = _now()
        doc = {**data, "status": "pending", "created_at": now, "updated_at": now}
        result = await self.appointments.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _out(doc)

    async def list_appointments(self, student_username: str | None = None) -> list:
        query = {}
        if student_username:
            query["student_username"] = student_username
        cursor = self.appointments.find(query).sort("date", -1)
        return [_out(doc) async for doc in cursor]

    async def get_appointment(self, appt_id: str) -> dict | None:
        try:
            doc = await self.appointments.find_one({"_id": ObjectId(appt_id)})
        except Exception:
            return None
        return _out(doc) if doc else None

    async def update_appointment_status(self, appt_id: str, status: str, teacher_note: str | None = None) -> dict | None:
        update = {"status": status, "updated_at": _now()}
        if teacher_note is not None:
            update["teacher_note"] = teacher_note
        result = await self.appointments.find_one_and_update(
            {"_id": ObjectId(appt_id)},
            {"$set": update},
            return_document=True
        )
        return _out(result) if result else None

    async def delete_appointment(self, appt_id: str) -> bool:
        result = await self.appointments.delete_one({"_id": ObjectId(appt_id)})
        return result.deleted_count > 0
