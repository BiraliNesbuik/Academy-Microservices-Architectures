from pydantic import BaseModel
from typing import Optional

class Course(BaseModel):
    title: str
    level: str
    price: float
    is_active: bool = True

class CourseResponse(Course):
    id: str

class Purchase(BaseModel):
    username: str
    course_id: str