import json
import logging
from fastapi import FastAPI, Header, Response, Request
from fastapi.responses import JSONResponse
import requests
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

logger = logging.getLogger("dispatcher")
logger.setLevel(logging.INFO)

SECRET_KEY = "gizli_anahtar_123"
ALGORITHM = "HS256"

MONGO_URL = "mongodb://mongo:27017"
DB_NAME = "dispatcher_db"

EXAM_SERVICE_URL = "http://exam-service:8000"
COURSE_SERVICE_URL = "http://course-service:8000"

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.state.db = app.state.mongo_client[DB_NAME]
    yield
    app.state.mongo_client.close()

app = FastAPI(lifespan=lifespan)

async def check_permission(db, role: str, service_prefix: str) -> bool:
    collection = db["permissions"]
    permission = await collection.find_one({"service": service_prefix})
    if not permission:
        return True
    return role in permission.get("allowed_roles", [])

def verify_and_decode_token(authorization: str | None) -> dict | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def _is_error_body(response_text: str) -> bool:
    try:
        body = json.loads(response_text)
        return body.get("error") is True
    except (json.JSONDecodeError, AttributeError):
        return False

@app.get("/exam/{path:path}")
async def route_to_exam_service(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"exam servisine istek: /{path}")

    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized or Invalid Token"})

    user_role = payload.get("role")
    db = request.app.state.db
    has_permission = await check_permission(db, user_role, "exam")
    if not has_permission:
        return JSONResponse(status_code=403, content={"error": "Forbidden: Rolünüzün yetkisi yok"})

    try:
        target_url = f"{EXAM_SERVICE_URL}/{path}"
        ms_response = requests.get(target_url, timeout=2)
        if ms_response.status_code == 200 and _is_error_body(ms_response.text):
            return JSONResponse(status_code=500, content={"error": "Internal Error"})
        return JSONResponse(status_code=ms_response.status_code, content=ms_response.json())
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.get("/course/{path:path}")
async def route_to_course_service(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"course servisine istek: /{path}")

    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized or Invalid Token"})

    user_role = payload.get("role")
    db = request.app.state.db
    has_permission = await check_permission(db, user_role, "course")
    if not has_permission:
        return JSONResponse(status_code=403, content={"error": "Forbidden: Rolünüzün yetkisi yok"})

    try:
        target_url = f"{COURSE_SERVICE_URL}/{path}"
        ms_response = requests.get(target_url, timeout=2)
        if ms_response.status_code == 200 and _is_error_body(ms_response.text):
            return JSONResponse(status_code=500, content={"error": "Internal Error"})
        return JSONResponse(status_code=ms_response.status_code, content=ms_response.json())
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)