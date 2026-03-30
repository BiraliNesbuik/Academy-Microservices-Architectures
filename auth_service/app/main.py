from fastapi import FastAPI, Header, HTTPException, Request, Depends
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.user import UserRegister, UserLogin, TokenResponse
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

MONGO_URL = "mongodb://mongo:27017"
DB_NAME = "auth_db"

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.state.db = app.state.mongo_client[DB_NAME]
    yield
    app.state.mongo_client.close()

app = FastAPI(lifespan=lifespan)

# Bağımlılıklar (Dependencies)
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