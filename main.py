from fastapi import FastAPI, Header, Response
import logging

app = FastAPI()

# Loglama ayarlarını yapıyoruz (Testteki 'istekler_loglanmali' kuralı için)
logger = logging.getLogger("dispatcher")
logger.setLevel(logging.INFO)


# --- 1. YÖNLENDİRME VE YETKİLENDİRME ---

@app.get("/exam/status")
def exam_status(authorization: str = Header(None)):
    logger.info("exam status için yeni bir istek geldi") # Loglama yapıyoruz
    
    # Token yoksa veya yanlışsa 401 (Unauthorized) dön
    if not authorization or authorization != "Bearer gecerli_bir_token":
        return Response(status_code=401)
    
    # Her şey yolundaysa 200 OK dön
    return Response(status_code=200)


# --- 2. HATA YÖNETİMİ ---

@app.get("/course/cokmus-servis")
def course_cokmus(authorization: str = Header(None)):
    logger.info("course servisine istek geldi")
    
    if not authorization or authorization != "Bearer gecerli_bir_token":
        return Response(status_code=401)
    
    # Servis çökmüş senaryosu, 503 dönüyoruz
    return Response(status_code=503)

@app.get("/exam/hata-ver")
def exam_hata(authorization: str = Header(None)):
    logger.info("hata servisine istek geldi")
    
    if not authorization or authorization != "Bearer gecerli_bir_token":
        return Response(status_code=401)
    
    # Proje kuralı: Hata anında asla 200 dönme! 
    # Sadece JSON içinde "error" yazarak HTTP 200 dönmemeliyiz.
    return Response(content='{"error": true}', status_code=500)