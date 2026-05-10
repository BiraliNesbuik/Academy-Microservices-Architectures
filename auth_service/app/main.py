from fastapi import FastAPI, Header, HTTPException, Request, Depends
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.user import UserRegister, UserLogin, TokenResponse
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

MONGO_URL = "mongodb://auth-mongo:27017"
DB_NAME = "auth_db"

SEED_USERS = [
    {"username": "emir",     "password": "123", "role": "admin"},
    {"username": "ogr1",     "password": "123", "role": "student"},
    {"username": "ogr2",     "password": "123", "role": "student"},
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.state.db = app.state.mongo_client[DB_NAME]

    repo = UserRepository(app.state.db)
    from app.services.auth_service import AuthService as _AS
    svc = _AS(repo)
    from app.models.user import UserRegister
    for u in SEED_USERS:
        if not await repo.username_exists(u["username"]):
            await svc.register(UserRegister(username=u["username"], password=u["password"], role=u["role"]))

    yield
    app.state.mongo_client.close()

app = FastAPI(lifespan=lifespan)

def get_database(request: Request):
    return request.app.state.db

def get_auth_service(db = Depends(get_database)):
    repo = UserRepository(db)
    return AuthService(repo)

@app.post("/auth/register", status_code=201)
async def register(data: UserRegister, service: AuthService = Depends(get_auth_service)):
    if not await service.register(data):
        raise HTTPException(status_code=409, detail="Kullanıcı zaten var")
    return {"message": "Kayıt başarılı"}

@app.post("/auth/login")
async def login(data: UserLogin, service: AuthService = Depends(get_auth_service)):
    token = await service.login(data.username, data.password)
    if not token:
        raise HTTPException(status_code=401, detail="Hatalı kullanıcı adı veya şifre")
    return TokenResponse(access_token=token)

@app.get("/auth/verify")
async def verify(authorization: str = Header(None), service: AuthService = Depends(get_auth_service)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token bulunamadı")
    token = authorization.split(" ")[1]
    payload = service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Geçersiz token")
    return {"username": payload["sub"], "role": payload["role"]}

@app.get("/auth/users")
async def get_all_users(authorization: str = Header(None), service: AuthService = Depends(get_auth_service)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token bulunamadı")
    token = authorization.split(" ")[1]
    payload = service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Geçersiz token")
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Sadece admin erişebilir")
    return await service.get_all_users()

@app.get("/auth/user/{username}")
async def get_user(username: str, authorization: str = Header(None), service: AuthService = Depends(get_auth_service)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token bulunamadı")
    token = authorization.split(" ")[1]
    payload = service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Geçersiz token")
    user = await service.get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    del user["hashed_password"]
    return user

@app.put("/auth/user/{username}")
async def update_password(username: str, data: dict, authorization: str = Header(None), service: AuthService = Depends(get_auth_service)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token bulunamadı")
    token = authorization.split(" ")[1]
    payload = service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Geçersiz token")
    if payload.get("role") != "admin" and payload.get("sub") != username:
        raise HTTPException(status_code=403, detail="Yetkisiz işlem")
    updated = await service.update_password(username, data.get("password"))
    if not updated:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return {"message": "Şifre güncellendi"}

@app.delete("/auth/user/{username}")
async def delete_user(username: str, authorization: str = Header(None), service: AuthService = Depends(get_auth_service)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token bulunamadı")
    token = authorization.split(" ")[1]
    payload = service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Geçersiz token")
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Sadece admin silebilir")
    deleted = await service.delete_user(username)
    if not deleted:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return {"message": "Kullanıcı silindi"}