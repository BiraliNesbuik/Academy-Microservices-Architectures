import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.models.booking import (
    SlotCreate, SlotResponse,
    AppointmentCreate, AppointmentStatusUpdate, AppointmentResponse
)
from app.repositories.booking_repository import BookingRepository

MONGO_URL = os.getenv("MONGO_URL", "mongodb://booking-mongo:27017")
DB_NAME = "booking_db"

VALID_STATUSES = {"approved", "rejected", "cancelled"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.state.db = app.state.mongo_client[DB_NAME]
    yield
    app.state.mongo_client.close()


app = FastAPI(lifespan=lifespan)


def get_database() -> AsyncIOMotorDatabase:
    return app.state.db


def get_repo(db: AsyncIOMotorDatabase = Depends(get_database)) -> BookingRepository:
    return BookingRepository(db)


# ── SLOT ENDPOINT'LERİ ─────────────────────────────────────────────

@app.get("/slots", response_model=list[SlotResponse])
async def list_slots(only_available: bool = False, repo: BookingRepository = Depends(get_repo)):
    return await repo.list_slots(only_available=only_available)


@app.post("/slots", response_model=SlotResponse, status_code=201)
async def create_slot(data: SlotCreate, repo: BookingRepository = Depends(get_repo)):
    return await repo.create_slot(data.model_dump())


@app.delete("/slots/{slot_id}", status_code=204)
async def delete_slot(slot_id: str, repo: BookingRepository = Depends(get_repo)):
    slot = await repo.get_slot(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot bulunamadı")
    if not slot["is_available"]:
        raise HTTPException(status_code=409, detail="Onaylı randevusu olan slot silinemez")
    deleted = await repo.delete_slot(slot_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Slot bulunamadı")


# ── APPOINTMENT ENDPOINT'LERİ ──────────────────────────────────────

@app.get("/appointments", response_model=list[AppointmentResponse])
async def list_appointments(student_username: str = None, repo: BookingRepository = Depends(get_repo)):
    return await repo.list_appointments(student_username=student_username)


@app.post("/appointments", response_model=AppointmentResponse, status_code=201)
async def create_appointment(data: AppointmentCreate, repo: BookingRepository = Depends(get_repo)):
    slot = await repo.get_slot(data.slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot bulunamadı")
    if not slot["is_available"]:
        raise HTTPException(status_code=409, detail="Bu slot artık müsait değil")

    appt = await repo.create_appointment(data.model_dump())
    await repo.mark_slot_unavailable(data.slot_id)
    return appt


@app.put("/appointments/{appt_id}", response_model=AppointmentResponse)
async def update_appointment(appt_id: str, data: AppointmentStatusUpdate, repo: BookingRepository = Depends(get_repo)):
    if data.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Geçersiz durum. Kabul edilenler: {VALID_STATUSES}")

    appt = await repo.get_appointment(appt_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Randevu bulunamadı")

    updated = await repo.update_appointment_status(appt_id, data.status, data.teacher_note)

    # Randevu iptal/reddedilirse slot tekrar müsait olur
    if data.status in {"rejected", "cancelled"}:
        await repo.mark_slot_available(appt["slot_id"])

    return updated


@app.delete("/appointments/{appt_id}", status_code=204)
async def delete_appointment(appt_id: str, repo: BookingRepository = Depends(get_repo)):
    appt = await repo.get_appointment(appt_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Randevu bulunamadı")

    deleted = await repo.delete_appointment(appt_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Randevu bulunamadı")

    # Silinen randevunun slotunu serbest bırak
    if appt["status"] not in {"rejected", "cancelled"}:
        await repo.mark_slot_available(appt["slot_id"])
