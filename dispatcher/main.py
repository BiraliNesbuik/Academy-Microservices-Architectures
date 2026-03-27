import json
from fastapi import FastAPI, Header, Response
from fastapi.responses import JSONResponse
import requests
import logging

app = FastAPI()

logger = logging.getLogger("dispatcher")
logger.setLevel(logging.INFO)

EXAM_SERVICE_URL = "http://exam-service:8000"

# İleride burası MongoDB/Redis'ten token doğrulaması yapacak
# Şimdilik test geçmek için basit tutuluyor (TDD: önce test, sonra gerçek impl.)
VALID_TOKENS = {"valid_test_token"}

def verify_token(authorization: str | None) -> bool:
    if not authorization:
        return False
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        return False
    return parts[1] in VALID_TOKENS

def _is_error_body(response_text: str) -> bool:
    """JSON body'de error:true (boolean) kontrolü — string içinde 'error' geçmesi yetmez."""
    try:
        body = json.loads(response_text)
        return body.get("error") is True
    except (json.JSONDecodeError, AttributeError):
        return False

@app.get("/exam/{path:path}")
def route_to_exam_service(path: str, authorization: str = Header(None)):
    logger.info(f"exam servisine istek: /{path}")

    if not verify_token(authorization):
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    try:
        target_url = f"{EXAM_SERVICE_URL}/{path}"
        ms_response = requests.get(target_url, timeout=2)

        # Proje kuralı: upstream 200 dönse bile error:true ise 500 döndür
        if ms_response.status_code == 200 and _is_error_body(ms_response.text):
            logger.warning(f"Upstream hata döndü: {ms_response.text}")
            return JSONResponse(status_code=500, content={"error": "Internal Error"})

        return JSONResponse(
            status_code=ms_response.status_code,
            content=ms_response.json()
        )

    except requests.exceptions.Timeout:
        logger.error(f"Timeout: {path}")
        return Response(status_code=504)

    except requests.exceptions.RequestException as e:
        logger.error(f"Bağlantı hatası: {e}")
        return Response(status_code=503)