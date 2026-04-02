from fastapi import FastAPI, Depends, Request, HTTPException
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.course import Course, Purchase
from app.repositories.course_repository import CourseRepository

MONGO_URL = "mongodb://course-mongo:27017"
DB_NAME = "course_db"

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.state.db = app.state.mongo_client[DB_NAME]
    yield
    app.state.mongo_client.close()

app = FastAPI(lifespan=lifespan)

def get_course_repository(request: Request):
    return CourseRepository(request.app.state.db)

@app.post("/courses", status_code=201)
async def create_course(course: Course, repo: CourseRepository = Depends(get_course_repository)):
    course_id = await repo.create_course(course)
    return {"id": course_id, "message": "Kurs oluşturuldu"}

@app.get("/courses")
async def list_courses(repo: CourseRepository = Depends(get_course_repository)):
    return await repo.get_all_courses()

@app.post("/courses/{course_id}/purchase", status_code=201)
async def purchase_course(course_id: str, purchase: Purchase, repo: CourseRepository = Depends(get_course_repository)):
    course = await repo.get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Kurs bulunamadı")
    if not course["is_active"]:
        raise HTTPException(status_code=400, detail="Kurs aktif değil")
    purchase_id = await repo.purchase_course(purchase)
    return {"id": purchase_id, "message": "Satın alma başarılı"}