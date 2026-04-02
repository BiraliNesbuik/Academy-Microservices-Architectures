from pydantic import BaseModel
from typing import Optional

class Course(BaseModel):
    title: str
    level: str  # Test 'B2' gönderiyor
    price: float
    is_active: bool = True

class CourseResponse(Course):
    id: str