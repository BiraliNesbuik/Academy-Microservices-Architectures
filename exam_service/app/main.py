from fastapi import FastAPI, Depends, Request, HTTPException
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.exam import Exam, ExamSession, AnswerSubmit
from app.repositories.exam_repository import ExamRepository

MONGO_URL = "mongodb://exam-mongo:27017"
DB_NAME = "exam_db"

SAMPLE_EXAMS = [
    {
        "title": "İngilizce A1 Seviye Tespit Sınavı",
        "duration_minutes": 30,
        "is_active": True,
        "questions": [
            {"question_text": "What is 'apple' in Turkish?", "options": ["Elma", "Armut", "Kiraz", "Üzüm"], "correct_answer": "Elma"},
            {"question_text": "What is 'house' in Turkish?", "options": ["Araba", "Ev", "Okul", "Bahçe"], "correct_answer": "Ev"},
            {"question_text": "Choose the correct verb: She ___ a teacher.", "options": ["am", "are", "is", "be"], "correct_answer": "is"},
        ]
    },
    {
        "title": "İngilizce B2 Seviye Tespit Sınavı",
        "duration_minutes": 45,
        "is_active": True,
        "questions": [
            {"question_text": "Choose the correct form: By the time she arrived, he ___ left.", "options": ["has", "had", "have", "was"], "correct_answer": "had"},
            {"question_text": "What does 'ubiquitous' mean?", "options": ["Rare", "Everywhere", "Unique", "Ancient"], "correct_answer": "Everywhere"},
        ]
    }
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.state.db = app.state.mongo_client[DB_NAME]
    count = await app.state.db["exams"].count_documents({})
    if count == 0:
        await app.state.db["exams"].insert_many(SAMPLE_EXAMS)
    yield
    app.state.mongo_client.close()

app = FastAPI(lifespan=lifespan)

def get_exam_repository(request: Request):
    return ExamRepository(request.app.state.db)

@app.post("/exams", status_code=201)
async def create_exam(exam: Exam, repo: ExamRepository = Depends(get_exam_repository)):
    exam_id = await repo.create_exam(exam)
    return {"id": exam_id, "message": "Sınav oluşturuldu"}

@app.get("/exams")
async def list_exams(repo: ExamRepository = Depends(get_exam_repository)):
    return await repo.get_all_exams()

@app.get("/exams/{exam_id}")
async def get_exam(exam_id: str, repo: ExamRepository = Depends(get_exam_repository)):
    exam = await repo.get_exam_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Sınav bulunamadı")
    return exam

@app.post("/exams/{exam_id}/start", status_code=201)
async def start_exam(exam_id: str, session: ExamSession, repo: ExamRepository = Depends(get_exam_repository)):
    exam = await repo.get_exam_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Sınav bulunamadı")
    if not exam["is_active"]:
        raise HTTPException(status_code=400, detail="Sınav aktif değil")
    session_id = await repo.start_exam(session)
    if not session_id:
        raise HTTPException(status_code=409, detail="Bu sınava zaten girildi")
    return {"id": session_id, "message": "Sınav başladı"}

@app.post("/exams/{exam_id}/answer")
async def save_answer(exam_id: str, answer: AnswerSubmit, repo: ExamRepository = Depends(get_exam_repository)):
    saved = await repo.save_answer(exam_id, answer)
    if not saved:
        raise HTTPException(status_code=400, detail="Cevap kaydedilemedi")
    return {"message": "Cevap kaydedildi"}

@app.post("/exams/{exam_id}/submit")
async def submit_exam(exam_id: str, session: ExamSession, repo: ExamRepository = Depends(get_exam_repository)):
    score = await repo.submit_exam(exam_id, session.username)
    if score is None:
        raise HTTPException(status_code=400, detail="Aktif oturum bulunamadı")
    return {"message": "Sınav tamamlandı", "score": score}

@app.get("/exams/{exam_id}/result/{username}")
async def get_result(exam_id: str, username: str, repo: ExamRepository = Depends(get_exam_repository)):
    result = await repo.get_result(exam_id, username)
    if not result:
        raise HTTPException(status_code=404, detail="Sonuç bulunamadı")
    return result