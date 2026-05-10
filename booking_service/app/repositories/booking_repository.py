from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc)


def _slot_out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


def _appt_out(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


class BookingRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.slots = db["slots"]
        self.appointments = db["appointments"]

    # ── SLOT işlemleri ─────────────────────────────────────────

    async def create_slot(self, data: dict) -> dict:
        doc = {**data, "is_available": True, "created_at": _now()}
        result = await self.slots.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _slot_out(doc)

    async def list_slots(self, only_available: bool = False) -> list:
        query = {"is_available": True} if only_available else {}
        cursor = self.slots.find(query).sort("date", 1)
        return [_slot_out(doc) async for doc in cursor]

    async def get_slot(self, slot_id: str) -> dict | None:
        try:
            doc = await self.slots.find_one({"_id": ObjectId(slot_id)})
        except Exception:
            return None
        return _slot_out(doc) if doc else None

    async def mark_slot_unavailable(self, slot_id: str):
        await self.slots.update_one(
            {"_id": ObjectId(slot_id)},
            {"$set": {"is_available": False}}
        )

    async def mark_slot_available(self, slot_id: str):
        await self.slots.update_one(
            {"_id": ObjectId(slot_id)},
            {"$set": {"is_available": True}}
        )

    async def delete_slot(self, slot_id: str) -> bool:
        result = await self.slots.delete_one({"_id": ObjectId(slot_id)})
        return result.deleted_count > 0

    # ── APPOINTMENT işlemleri ───────────────────────────────────

    async def create_appointment(self, data: dict) -> dict:
        now = _now()
        doc = {**data, "status": "pending", "created_at": now, "updated_at": now}
        result = await self.appointments.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _appt_out(doc)

    async def list_appointments(self, student_username: str | None = None) -> list:
        query = {}
        if student_username:
            query["student_username"] = student_username
        cursor = self.appointments.find(query).sort("created_at", -1)
        return [_appt_out(doc) async for doc in cursor]

    async def get_appointment(self, appt_id: str) -> dict | None:
        try:
            doc = await self.appointments.find_one({"_id": ObjectId(appt_id)})
        except Exception:
            return None
        return _appt_out(doc) if doc else None

    async def update_appointment_status(self, appt_id: str, status: str, teacher_note: str | None = None) -> dict | None:
        update = {"status": status, "updated_at": _now()}
        if teacher_note is not None:
            update["teacher_note"] = teacher_note
        result = await self.appointments.find_one_and_update(
            {"_id": ObjectId(appt_id)},
            {"$set": update},
            return_document=True
        )
        return _appt_out(result) if result else None

    async def delete_appointment(self, appt_id: str) -> bool:
        result = await self.appointments.delete_one({"_id": ObjectId(appt_id)})
        return result.deleted_count > 0
