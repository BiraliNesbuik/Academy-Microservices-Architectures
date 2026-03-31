from locust import HttpUser, task, between

class DilAkademisiUser(HttpUser):
    wait_time = between(1, 3) # Kullanıcıların her istek arası 1 ile 3 saniye beklemesini sağlar

    @task(1)
    def login_test(self):
        # Dispatcher üzerinden Auth servisine login isteği atıyoruz
        payload = {"username": "test_ogrenci", "password": "123"}
        self.client.post("/auth/login", json=payload)

    @task(2)
    def invalid_route_test(self):
        # Dispatcher'ın olmayan sayfalara 404 dönme hızını ölçüyoruz
        self.client.get("/olmayan-bir-sayfa")