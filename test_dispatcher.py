import pytest
from fastapi.testclient import TestClient

# Henüz yazmadığımız asıl Dispatcher kodumuzu içe aktarmaya çalışıyoruz
# TDD mantığı gereği bu dosya henüz yok, bu yüzden ilk başta hata alacağız (RED aşaması)
from main import app 

client = TestClient(app)

# --- 1. YÖNLENDİRME (ROUTING) TESTLERİ ---

def test_yonlendirme_sinav_servisi():
    """ /exam endpoint'ine gelen istekler doğru yönlendirilmeli """
    headers = {"Authorization": "Bearer gecerli_bir_token"}
    response = client.get("/exam/status", headers=headers)
    
    # Sınav servisi ayaktaysa başarılı (200 OK) dönmeli
    assert response.status_code == 200

def test_yonlendirme_bulunamadi():
    """ Sistemde olmayan, saçma bir URL'ye istek atıldığında 404 dönmeli """
    response = client.get("/olmayan-sayfa")
    assert response.status_code == 404


# --- 2. YETKİLENDİRME (AUTH) TESTLERİ ---
# Yetkilendirme kontrolleri tek merkezden yapılmalıdır [cite: 40]

def test_yetkisiz_giris_token_yok():
    """ İstekte token yoksa doğrudan reddedilmeli (401 Unauthorized) """
    response = client.get("/exam/status") # Bilerek header (token) eklemiyoruz
    assert response.status_code == 401

def test_yetkisiz_giris_gecersiz_token():
    """ Yanlış/sahte bir token gönderilirse reddedilmeli """
    headers = {"Authorization": "Bearer sahte_ve_gecersiz_token"}
    response = client.get("/exam/status", headers=headers)
    assert response.status_code == 401


# --- 3. HATA YÖNETİMİ (ERROR HANDLING) TESTLERİ ---

def test_hata_durumunda_200_donmemeli():
    """ Hata oluştuğunda bile her zaman HTTP 200 OK dönülmemelidir kuralı [cite: 42] """
    headers = {"Authorization": "Bearer gecerli_bir_token"}
    response = client.get("/exam/hata-ver", headers=headers)
    
    # Cevap metninde "error" kelimesi geçiyorsa, HTTP kodu KESİNLİKLE 200 olmamalıdır
    if "error" in response.text.lower():
        assert response.status_code != 200

def test_servis_cokmusse_503_donmeli():
    """ Ulaşılamayan servisler ve hatalar için uygun hata kodları (HTTP 4xx, HTTP 5xx vb.) dönülmelidir [cite: 41] """
    headers = {"Authorization": "Bearer gecerli_bir_token"}
    response = client.get("/course/cokmus-servis", headers=headers)
    
    # 500, 502, 503 veya 504 gibi sunucu hatası kodlarından biri dönmeli
    assert response.status_code in [500, 502, 503, 504]


# --- 4. LOGLAMA TESTLERİ ---

def test_istekler_loglanmali(caplog):
    """ Tüm trafik ve yönetici işlemleri loglanmalıdır [cite: 41] """
    headers = {"Authorization": "Bearer gecerli_bir_token"}
    client.get("/exam/status", headers=headers)
    
    # Kaydedilen log metinlerinde belirlediğimiz anahtar kelimeler geçmeli
    assert "istek" in caplog.text.lower() or "request" in caplog.text.lower()