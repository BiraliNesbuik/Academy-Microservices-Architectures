from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SlotCreate(BaseModel):
    date: str          # "2026-05-15"
    start_time: str    # "14:00"
    end_time: str      # "15:00"
    note: Optional[str] = None


class SlotResponse(BaseModel):
    id: str
    date: str
    start_time: str
    end_time: str
    note: Optional[str] = None
    is_available: bool
    created_at: datetime


class AppointmentCreate(BaseModel):
    slot_id: str
    student_username: str
    student_note: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    # teacher: "approved" / "rejected"
    # student: "cancelled"
    status: str
    teacher_note: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: str
    slot_id: str
    student_username: str
    student_note: Optional[str] = None
    teacher_note: Optional[str] = None
    status: str   # pending / approved / rejected / cancelled
    created_at: datetime
    updated_at: datetime
