from pydantic import BaseModel
from typing import Optional, List

class Question(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str

class Exam(BaseModel):
    title: str
    duration_minutes: int
    questions: List[Question]
    is_active: bool = True

class ExamSession(BaseModel):
    username: str
    exam_id: str

class AnswerSubmit(BaseModel):
    username: str
    question_text: str
    answer: str