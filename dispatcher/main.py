import json
import logging
import os
from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
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

MONGO_URL = "mongodb://dispatcher-mongo:27017"
DB_NAME = "dispatcher_db"

EXAM_SERVICE_URL = "http://exam-service:8000"
COURSE_SERVICE_URL = "http://course-service:8000"
AUTH_SERVICE_URL = "http://auth-service:8001"

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.state.db = app.state.mongo_client[DB_NAME]

    count = await app.state.db["permissions"].count_documents({})
    if count == 0:
        await app.state.db["permissions"].insert_many([
            {"service": "exam",   "allowed_roles": ["teacher", "student", "admin"]},
            {"service": "course", "allowed_roles": ["teacher", "student", "admin"]},
        ])

    yield
    app.state.mongo_client.close()

app = FastAPI(lifespan=lifespan)

async def get_log_count():
    return await app.state.db.traffic_logs.count_documents({})

@app.middleware("http")
async def log_traffic_to_mongo(request: Request, call_next):
    response = await call_next(request)
    log_entry = {
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "timestamp": datetime.now(timezone.utc)
    }
    await app.state.db.traffic_logs.insert_one(log_entry)
    return response

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

def _forward_response(ms_response):
    if ms_response.status_code == 200 and _is_error_body(ms_response.text):
        return JSONResponse(status_code=500, content={"error": "Internal Error"})
    return Response(
        content=ms_response.content,
        status_code=ms_response.status_code,
        media_type=ms_response.headers.get("content-type", "application/json")
    )

# ── EXAM SERVİSİ ──────────────────────────────────────────────

@app.get("/exam/{path:path}")
async def exam_get(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"exam servisine GET isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "exam"):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        ms_response = requests.get(
            f"{EXAM_SERVICE_URL}/{path}",
            params=dict(request.query_params),
            timeout=2
        )
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.post("/exam/{path:path}")
async def exam_post(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"exam servisine POST isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "exam"):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.post(f"{EXAM_SERVICE_URL}/{path}", json=body, timeout=2)
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.put("/exam/{path:path}")
async def exam_put(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"exam servisine PUT isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "exam"):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.put(f"{EXAM_SERVICE_URL}/{path}", json=body, timeout=2)
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.delete("/exam/{path:path}")
async def exam_delete(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"exam servisine DELETE isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "exam"):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        ms_response = requests.delete(f"{EXAM_SERVICE_URL}/{path}", timeout=2)
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

# ── COURSE SERVİSİ ─────────────────────────────────────────────

@app.get("/course/{path:path}")
async def course_get(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"course servisine GET isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "course"):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        ms_response = requests.get(
            f"{COURSE_SERVICE_URL}/{path}",
            params=dict(request.query_params),
            timeout=2
        )
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.post("/course/{path:path}")
async def course_post(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"course servisine POST isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "course"):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.post(f"{COURSE_SERVICE_URL}/{path}", json=body, timeout=2)
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.post("/course/courses/{course_id}/purchase")
async def course_purchase(course_id: str, request: Request, authorization: str = Header(None)):
    logger.info(f"course servisine satın alma isteği: {course_id}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "course"):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.post(
            f"{COURSE_SERVICE_URL}/courses/{course_id}/purchase",
            json=body,
            timeout=2
        )
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.put("/course/{path:path}")
async def course_put(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"course servisine PUT isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "course"):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.put(f"{COURSE_SERVICE_URL}/{path}", json=body, timeout=2)
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.delete("/course/{path:path}")
async def course_delete(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"course servisine DELETE isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "course"):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        ms_response = requests.delete(f"{COURSE_SERVICE_URL}/{path}", timeout=2)
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

# ── AUTH SERVİSİ YÖNLENDİRMESİ ───────────────────────────────────

@app.post("/auth/{path:path}")
async def auth_post(path: str, request: Request):
    logger.info(f"Auth servisine POST isteği: /{path}")
    try:
        body = await request.json()
        ms_response = requests.post(f"{AUTH_SERVICE_URL}/auth/{path}", json=body, timeout=15)
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)