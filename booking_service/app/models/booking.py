from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AppointmentCreate(BaseModel):
    date: str                        # "2026-05-15"
    start_time: str                  # "14:00"
    student_username: str
    student_note: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    status: str                      # approved / rejected / cancelled
    teacher_note: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: str
    date: str
    start_time: str
    student_username: str
    student_note: Optional[str] = None
    teacher_note: Optional[str] = None
    status: str                      # pending / approved / rejected / cancelled
    created_at: datetime
    updated_at: datetime
