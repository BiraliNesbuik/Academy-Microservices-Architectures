from locust import HttpUser, task, between

class DilAkademisiUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Test başlarken bir kez kullanıcıyı kayıt etmeyi deneriz.
        # Böylece login işleminde veritabanında kullanıcı hazır olur.
        self.client.post("/auth/register", json={"username": "test_ogrenci", "password": "123", "role": "student"})

    @task(2)
    def login_test(self):
        # Artık kullanıcı var olduğu için 200 OK dönecek ve yeşil olacak
        self.client.post("/auth/login", json={"username": "test_ogrenci", "password": "123"})

    @task(1)
    def invalid_route_test(self):
        # 404 beklediğimizi Locust'a açıkça söylüyoruz ki bunu hata değil 'başarı' saysın
        with self.client.get("/olmayan-bir-sayfa", catch_response=True) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Beklenmeyen kod: {response.status_code}")