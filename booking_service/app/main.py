import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.models.booking import (
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


# ── APPOINTMENT ENDPOINT'LERİ ──────────────────────────────────────

@app.get("/appointments", response_model=list[AppointmentResponse])
async def list_appointments(student_username: str = None, repo: BookingRepository = Depends(get_repo)):
    return await repo.list_appointments(student_username=student_username)


@app.post("/appointments", response_model=AppointmentResponse, status_code=201)
async def create_appointment(data: AppointmentCreate, repo: BookingRepository = Depends(get_repo)):
    return await repo.create_appointment(data.model_dump())


@app.put("/appointments/{appt_id}", response_model=AppointmentResponse)
async def update_appointment(appt_id: str, data: AppointmentStatusUpdate, repo: BookingRepository = Depends(get_repo)):
    if data.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Geçersiz durum. Kabul edilenler: {VALID_STATUSES}")

    appt = await repo.get_appointment(appt_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Randevu bulunamadı")

    return await repo.update_appointment_status(appt_id, data.status, data.teacher_note)


@app.delete("/appointments/{appt_id}", status_code=204)
async def delete_appointment(appt_id: str, repo: BookingRepository = Depends(get_repo)):
    appt = await repo.get_appointment(appt_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Randevu bulunamadı")
    deleted = await repo.delete_appointment(appt_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Randevu bulunamadı")
