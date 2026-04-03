from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.exam import Exam, ExamSession, AnswerSubmit
from bson import ObjectId
from datetime import datetime, timezone

class ExamRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.exams = db["exams"]
        self.sessions = db["sessions"]

    async def create_exam(self, exam: Exam):
        result = await self.exams.insert_one(exam.model_dump())
        return str(result.inserted_id)

    async def get_all_exams(self):
        cursor = self.exams.find()
        exams = []
        async for document in cursor:
            document["id"] = str(document["_id"])
            del document["_id"]
            exams.append(document)
        return exams

    async def get_exam_by_id(self, exam_id: str):
        document = await self.exams.find_one({"_id": ObjectId(exam_id)})
        if document:
            document["id"] = str(document["_id"])
            del document["_id"]
        return document

    async def start_exam(self, session: ExamSession):
        existing = await self.sessions.find_one({
            "username": session.username,
            "exam_id": session.exam_id
        })
        if existing:
            return None
        result = await self.sessions.insert_one({
            "username": session.username,
            "exam_id": session.exam_id,
            "started_at": datetime.now(timezone.utc),
            "answers": [],
            "submitted": False
        })
        return str(result.inserted_id)

    async def save_answer(self, exam_id: str, answer: AnswerSubmit):
        result = await self.sessions.update_one(
            {"username": answer.username, "exam_id": exam_id, "submitted": False},
            {"$push": {"answers": {
                "question_text": answer.question_text,
                "answer": answer.answer
            }}}
        )
        return result.modified_count > 0

    async def submit_exam(self, exam_id: str, username: str):
        session = await self.sessions.find_one({
            "username": username,
            "exam_id": exam_id,
            "submitted": False
        })
        if not session:
            return None

        exam = await self.get_exam_by_id(exam_id)
        if not exam:
            return None

        # Puanlama
        correct = 0
        for q in exam["questions"]:
            for a in session["answers"]:
                if a["question_text"] == q["question_text"] and a["answer"] == q["correct_answer"]:
                    correct += 1

        score = int((correct / len(exam["questions"])) * 100) if exam["questions"] else 0

        await self.sessions.update_one(
            {"username": username, "exam_id": exam_id},
            {"$set": {"submitted": True, "score": score, "submitted_at": datetime.now(timezone.utc)}}
        )
        return score

    async def get_result(self, exam_id: str, username: str):
        session = await self.sessions.find_one({
            "username": username,
            "exam_id": exam_id,
            "submitted": True
        })
        if session:
            session["id"] = str(session["_id"])
            del session["_id"]
        return session