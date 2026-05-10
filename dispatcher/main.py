import json
import logging
from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from fastapi import FastAPI, Header, Response, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from jose import jwt, JWTError
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
BOOKING_SERVICE_URL = "http://booking-service:8000"

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URL)
    app.state.db = app.state.mongo_client[DB_NAME]

    count = await app.state.db["permissions"].count_documents({})
    if count == 0:
        await app.state.db["permissions"].insert_many([
            # EXAM
            {"service": "exam", "method": "GET",    "allowed_roles": ["teacher", "student", "admin"]},
            {"service": "exam", "method": "POST",   "path": "exams$",  "allowed_roles": ["teacher", "admin"]},
            {"service": "exam", "method": "POST",   "path": "start",   "allowed_roles": ["student"]},
            {"service": "exam", "method": "POST",   "path": "answer",  "allowed_roles": ["student"]},
            {"service": "exam", "method": "POST",   "path": "submit",  "allowed_roles": ["student"]},
            {"service": "exam", "method": "PUT",    "allowed_roles": ["teacher", "admin"]},
            {"service": "exam", "method": "DELETE", "allowed_roles": ["teacher", "admin"]},
            # BOOKING
            {"service": "booking", "method": "GET",    "allowed_roles": ["teacher", "student", "admin"]},
            {"service": "booking", "method": "POST",   "path": "slots",        "allowed_roles": ["teacher", "admin"]},
            {"service": "booking", "method": "POST",   "path": "appointments", "allowed_roles": ["student"]},
            {"service": "booking", "method": "PUT",    "path": "appointments", "allowed_roles": ["teacher", "student", "admin"]},
            {"service": "booking", "method": "DELETE", "path": "slots",        "allowed_roles": ["teacher", "admin"]},
            {"service": "booking", "method": "DELETE", "path": "appointments", "allowed_roles": ["teacher", "admin"]},
            # COURSE
            {"service": "course", "method": "GET",    "allowed_roles": ["teacher", "student", "admin"]},
            {"service": "course", "method": "POST",   "path": "courses$", "allowed_roles": ["teacher", "admin"]},
            {"service": "course", "method": "POST",   "path": "purchase", "allowed_roles": ["student"]},
            {"service": "course", "method": "POST",   "path": "cart",     "allowed_roles": ["student"]},
            {"service": "course", "method": "DELETE", "path": "cart",     "allowed_roles": ["student"]},
            {"service": "course", "method": "PUT",    "allowed_roles": ["teacher", "admin"]},
            {"service": "course", "method": "DELETE", "allowed_roles": ["teacher", "admin"]},
        ])

    yield
    app.state.mongo_client.close()

app = FastAPI(lifespan=lifespan)

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

async def check_permission(db, role: str, service_prefix: str, method: str, path: str) -> bool:
    collection = db["permissions"]
    import re
    rules = collection.find({"service": service_prefix, "method": method})
    async for rule in rules:
        if "path" in rule:
            if re.search(rule["path"], path):
                return role in rule.get("allowed_roles", [])
        else:
            return role in rule.get("allowed_roles", [])
    return True

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
    if not await check_permission(request.app.state.db, payload.get("role"), "exam", "GET", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        ms_response = requests.get(
            f"{EXAM_SERVICE_URL}/{path}",
            params=dict(request.query_params),
            timeout=10
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
    if not await check_permission(request.app.state.db, payload.get("role"), "exam", "POST", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.post(f"{EXAM_SERVICE_URL}/{path}", json=body, timeout=10)
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
    if not await check_permission(request.app.state.db, payload.get("role"), "exam", "PUT", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.put(f"{EXAM_SERVICE_URL}/{path}", json=body, timeout=10)
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
    if not await check_permission(request.app.state.db, payload.get("role"), "exam", "DELETE", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        ms_response = requests.delete(f"{EXAM_SERVICE_URL}/{path}", timeout=10)
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
    if not await check_permission(request.app.state.db, payload.get("role"), "course", "GET", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        ms_response = requests.get(
            f"{COURSE_SERVICE_URL}/{path}",
            params=dict(request.query_params),
            timeout=10
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
    if not await check_permission(request.app.state.db, payload.get("role"), "course", "POST", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.post(f"{COURSE_SERVICE_URL}/{path}", json=body, timeout=10)
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
    if not await check_permission(request.app.state.db, payload.get("role"), "course", "POST", f"courses/{course_id}/purchase"):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.post(
            f"{COURSE_SERVICE_URL}/courses/{course_id}/purchase",
            json=body,
            timeout=10
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
    if not await check_permission(request.app.state.db, payload.get("role"), "course", "PUT", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.put(f"{COURSE_SERVICE_URL}/{path}", json=body, timeout=10)
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
    if not await check_permission(request.app.state.db, payload.get("role"), "course", "DELETE", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        ms_response = requests.delete(f"{COURSE_SERVICE_URL}/{path}", timeout=10)
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

# ── BOOKING SERVİSİ ───────────────────────────────────────────────

@app.get("/booking/{path:path}")
async def booking_get(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"booking servisine GET isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "booking", "GET", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        ms_response = requests.get(
            f"{BOOKING_SERVICE_URL}/{path}",
            params=dict(request.query_params),
            timeout=10
        )
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.post("/booking/{path:path}")
async def booking_post(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"booking servisine POST isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "booking", "POST", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.post(f"{BOOKING_SERVICE_URL}/{path}", json=body, timeout=10)
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.put("/booking/{path:path}")
async def booking_put(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"booking servisine PUT isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "booking", "PUT", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        body = await request.json()
        ms_response = requests.put(f"{BOOKING_SERVICE_URL}/{path}", json=body, timeout=10)
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.delete("/booking/{path:path}")
async def booking_delete(path: str, request: Request, authorization: str = Header(None)):
    logger.info(f"booking servisine DELETE isteği: /{path}")
    payload = verify_and_decode_token(authorization)
    if not payload:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    if not await check_permission(request.app.state.db, payload.get("role"), "booking", "DELETE", path):
        return JSONResponse(status_code=403, content={"error": "Forbidden"})
    try:
        ms_response = requests.delete(f"{BOOKING_SERVICE_URL}/{path}", timeout=10)
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

@app.get("/auth/users")
async def auth_get_users(request: Request, authorization: str = Header(None)):
    logger.info("Auth servisine GET users isteği")
    try:
        ms_response = requests.get(
            f"{AUTH_SERVICE_URL}/auth/users",
            headers={"Authorization": authorization},
            timeout=10
        )
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.get("/auth/user/{username}")
async def auth_get_user(username: str, request: Request, authorization: str = Header(None)):
    logger.info(f"Auth servisine GET user isteği: {username}")
    try:
        ms_response = requests.get(
            f"{AUTH_SERVICE_URL}/auth/user/{username}",
            headers={"Authorization": authorization},
            timeout=10
        )
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.put("/auth/user/{username}")
async def auth_update_user(username: str, request: Request, authorization: str = Header(None)):
    logger.info(f"Auth servisine PUT user isteği: {username}")
    try:
        body = await request.json()
        ms_response = requests.put(
            f"{AUTH_SERVICE_URL}/auth/user/{username}",
            json=body,
            headers={"Authorization": authorization},
            timeout=10
        )
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)

@app.delete("/auth/user/{username}")
async def auth_delete_user(username: str, request: Request, authorization: str = Header(None)):
    logger.info(f"Auth servisine DELETE user isteği: {username}")
    try:
        ms_response = requests.delete(
            f"{AUTH_SERVICE_URL}/auth/user/{username}",
            headers={"Authorization": authorization},
            timeout=10
        )
        return _forward_response(ms_response)
    except requests.exceptions.Timeout:
        return Response(status_code=504)
    except requests.exceptions.RequestException:
        return Response(status_code=503)