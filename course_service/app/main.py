from fastapi import FastAPI, Depends, Request
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.course import Course
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

# TESTİN BEKLEDİĞİ ROTA: /courses
@app.post("/courses", status_code=201)
async def create_course(course: Course, repo: CourseRepository = Depends(get_course_repository)):
    course_id = await repo.create_course(course)
    return {"id": course_id, "message": "Kurs oluşturuldu"}

@app.get("/courses")
async def list_courses(repo: CourseRepository = Depends(get_course_repository)):
    return await repo.get_all_courses()