from fastapi import FastAPI, Depends, Request, HTTPException
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.course import Course, Purchase, CartItem
from app.repositories.course_repository import CourseRepository

MONGO_URL = "mongodb://course-mongo:27017"
DB_NAME = "course_db"

SAMPLE_COURSES = [
    {"title": "İngilizce A1 - Başlangıç", "level": "A1", "price": 299.0, "is_active": True},
    {"title": "İngilizce B2 - Orta Üstü", "level": "B2", "price": 599.0, "is_active": True},
    {"title": "Almanca A1 - Başlangıç",   "level": "A1", "price": 349.0, "is_active": True},
    {"title": "İspanyolca A2",             "level": "A2", "price": 399.0, "is_active": True},
    {"title": "Fransızca C1 - İleri",      "level": "C1", "price": 799.0, "is_active": False},
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.state.db = app.state.mongo_client[DB_NAME]
    count = await app.state.db["courses"].count_documents({})
    if count == 0:
        await app.state.db["courses"].insert_many(SAMPLE_COURSES)
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

@app.get("/courses/my-purchases")
async def get_my_purchases(username: str, repo: CourseRepository = Depends(get_course_repository)):
    return await repo.get_purchases_by_username(username)

@app.get("/courses/cart")
async def get_cart(username: str, repo: CourseRepository = Depends(get_course_repository)):
    return await repo.get_cart(username)

@app.get("/courses/{course_id}")
async def get_course(course_id: str, repo: CourseRepository = Depends(get_course_repository)):
    course = await repo.get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Kurs bulunamadı")
    return course

@app.put("/courses/{course_id}")
async def update_course(course_id: str, course: Course, repo: CourseRepository = Depends(get_course_repository)):
    updated = await repo.update_course(course_id, course.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Kurs bulunamadı veya değişiklik yapılmadı")
    return {"message": "Kurs güncellendi"}

@app.delete("/courses/{course_id}")
async def delete_course(course_id: str, repo: CourseRepository = Depends(get_course_repository)):
    deleted = await repo.delete_course(course_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Kurs bulunamadı")
    return {"message": "Kurs silindi"}

@app.post("/courses/{course_id}/purchase", status_code=201)
async def purchase_course(course_id: str, purchase: Purchase, repo: CourseRepository = Depends(get_course_repository)):
    course = await repo.get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Kurs bulunamadı")
    if not course["is_active"]:
        raise HTTPException(status_code=400, detail="Kurs aktif değil")
    purchase_id = await repo.purchase_course(purchase)
    return {"id": purchase_id, "message": "Satın alma başarılı"}

@app.post("/courses/cart/add", status_code=201)
async def add_to_cart(item: CartItem, repo: CourseRepository = Depends(get_course_repository)):
    course = await repo.get_course_by_id(item.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Kurs bulunamadı")
    if not course["is_active"]:
        raise HTTPException(status_code=400, detail="Kurs aktif değil")
    result = await repo.add_to_cart(item.username, item.course_id)
    if not result:
        raise HTTPException(status_code=409, detail="Kurs zaten sepette")
    return {"message": "Kurs sepete eklendi"}

@app.delete("/courses/cart/{course_id}")
async def remove_from_cart(course_id: str, username: str, repo: CourseRepository = Depends(get_course_repository)):
    result = await repo.remove_from_cart(username, course_id)
    if not result:
        raise HTTPException(status_code=404, detail="Kurs sepette bulunamadı")
    return {"message": "Kurs sepetten çıkarıldı"}

@app.post("/courses/cart/checkout")
async def checkout_cart(item: CartItem, repo: CourseRepository = Depends(get_course_repository)):
    purchased = await repo.checkout_cart(item.username)
    if not purchased:
        raise HTTPException(status_code=400, detail="Sepet boş")
    return {"message": f"{len(purchased)} kurs satın alındı", "purchased": purchased}