from locust import HttpUser, task, between

class DilAkademisiUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        with self.client.post("/auth/register", json={
            "username": "test_ogrenci",
            "password": "123",
            "role": "student"
        }, catch_response=True) as response:
            if response.status_code in [201, 409]:
                response.success()

        response = self.client.post("/auth/login", json={
            "username": "test_ogrenci",
            "password": "123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")

    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(2)
    def login_test(self):
        self.client.post("/auth/login", json={
            "username": "test_ogrenci",
            "password": "123"
        })

    @task(3)
    def list_courses(self):
        if self.token:
            self.client.get("/course/courses", headers=self.auth_headers())

    @task(2)
    def list_exams(self):
        if self.token:
            self.client.get("/exam/exams", headers=self.auth_headers())

    @task(2)
    def get_single_course(self):
        if self.token:
            response = self.client.get("/course/courses", headers=self.auth_headers())
            if response.status_code == 200 and response.json():
                course_id = response.json()[0].get("id")
                if course_id:
                    self.client.get(f"/course/courses/{course_id}", headers=self.auth_headers())

    @task(1)
    def my_purchases(self):
        if self.token:
            self.client.get(
                "/course/courses/my-purchases",
                params={"username": "test_ogrenci"},
                headers=self.auth_headers()
            )

    @task(1)
    def invalid_route_test(self):
        with self.client.get("/olmayan-bir-sayfa", catch_response=True) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Beklenmeyen kod: {response.status_code}")