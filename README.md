# Academy Microservices Architecture

**Ekip Üyeleri:**
- Emir Tekin (231307062)
- Ediz Sevinçler (231307020)

**Tarih:** 05/04/2026

---

## 1. Giriş

### Problemin Tanımı
Günümüzde eğitim kurumlarında öğrenciler ders dışında kendilerini geliştirmek için yeterli dijital kaynaklara erişememektedir. Geleneksel monolitik sistemler, vize/final haftaları gibi yoğun dönemlerde yüksek trafik altında çökmekte ve öğrencilere kesintisiz hizmet sunamamaktadır.

### Amacımız
Bu projede öğrencilerin kurs satın alabileceği, sınav çözebileceği ve dil becerilerini geliştirebileceği ölçeklenebilir bir platform geliştirilmiştir. Sistem; mikroservis mimarisi, merkezi bir API Gateway (Dispatcher) ve bağımsız veritabanlarıyla yüksek trafik altında dahi kesintisiz çalışacak şekilde tasarlanmıştır.

---

## 2. Tasarım ve Teorik Altyapı

### 2.1 Literatür İncelemesi
Udemy, Coursera gibi modern eğitim platformları incelenmiştir. Bu platformların monolitik yapısının yarattığı ölçeklenebilirlik sorunları göz önünde bulundurularak mikroservis mimarisi benimsenmiştir. Martin Fowler'ın mikroservis tanımına göre, her servis bağımsız olarak deploy edilebilir, kendi veritabanına sahiptir ve servisler arası iletişim hafif protokollerle (HTTP/JSON) sağlanır.

### 2.2 RESTful Servisler ve Richardson Olgunluk Modeli

**RESTful Prensipler:**
- Kaynak odaklı URL tasarımı (/courses, /exams, /auth)
- Standart HTTP metodları (GET, POST, PUT, DELETE)
- Durumsuzluk (Statelessness) — her istek kendi token'ını taşır
- JSON formatında veri transferi
- İstemci-sunucu bağımsızlığı

**Richardson Olgunluk Modeli — Seviye 2:**

Projemiz RMM Seviye 2 standartlarını karşılamaktadır:

| Seviye | Açıklama | Projemizdeki Karşılığı |
|--------|----------|------------------------|
| Level 0 | Tek endpoint | ❌ Kullanılmadı |
| Level 1 | Kaynak bazlı URL | ✅ /courses, /exams, /auth |
| Level 2 | HTTP metodları | ✅ GET/POST/PUT/DELETE |
| Level 3 | HATEOAS | - |

### 2.3 Sınıf Yapıları

**Auth Service Sınıf Diyagramı:**

```mermaid
classDiagram
    class User {
        +str username
        +str hashed_password
        +str role
    }
    class UserRegister {
        +str username
        +str password
        +str role
    }
    class UserLogin {
        +str username
        +str password
    }
    class TokenResponse {
        +str access_token
        +str token_type
    }
    class UserRepository {
        +find_by_username()
        +create_user()
        +username_exists()
        +get_all_users()
        +update_user()
        +delete_user()
    }
    class AuthService {
        +hash_password()
        +verify_password()
        +create_token()
        +decode_token()
        +register()
        +login()
        +get_all_users()
        +update_password()
        +delete_user()
    }
    AuthService --> UserRepository
    UserRepository --> User
```

**Course Service Sınıf Diyagramı:**

```mermaid
classDiagram
    class Course {
        +str title
        +str level
        +float price
        +bool is_active
    }
    class Purchase {
        +str username
        +str course_id
    }
    class CartItem {
        +str username
        +str course_id
    }
    class CourseRepository {
        +create_course()
        +get_all_courses()
        +get_course_by_id()
        +purchase_course()
        +get_purchases_by_username()
        +update_course()
        +delete_course()
        +add_to_cart()
        +get_cart()
        +remove_from_cart()
        +checkout_cart()
    }
    CourseRepository --> Course
    CourseRepository --> Purchase
    CourseRepository --> CartItem
```

**Exam Service Sınıf Diyagramı:**

```mermaid
classDiagram
    class Question {
        +str question_text
        +list options
        +str correct_answer
    }
    class Exam {
        +str title
        +int duration_minutes
        +list questions
        +bool is_active
    }
    class ExamSession {
        +str username
        +str exam_id
    }
    class AnswerSubmit {
        +str username
        +str question_text
        +str answer
    }
    class ExamRepository {
        +create_exam()
        +get_all_exams()
        +get_exam_by_id()
        +start_exam()
        +save_answer()
        +submit_exam()
        +get_result()
    }
    Exam --> Question
    ExamRepository --> Exam
    ExamRepository --> ExamSession
    ExamRepository --> AnswerSubmit
```

### 2.4 Sequence Diyagramları

**Login ve Kurs Listeleme Akışı:**

```mermaid
sequenceDiagram
    participant Client
    participant Dispatcher
    participant AuthService
    participant CourseService
    participant MongoDB

    Client->>Dispatcher: POST /auth/login
    Dispatcher->>AuthService: POST /auth/login
    AuthService->>MongoDB: Kullanıcı sorgula
    MongoDB-->>AuthService: Kullanıcı verisi
    AuthService-->>Dispatcher: JWT Token
    Dispatcher-->>Client: 200 OK + Token

    Client->>Dispatcher: GET /course/courses (Bearer Token)
    Dispatcher->>Dispatcher: Token doğrula
    Dispatcher->>Dispatcher: Yetki kontrol (MongoDB permissions)
    Dispatcher->>CourseService: GET /courses
    CourseService->>MongoDB: Kursları çek
    MongoDB-->>CourseService: Kurs listesi
    CourseService-->>Dispatcher: Kurs listesi
    Dispatcher-->>Client: 200 OK + Kurslar
```

**Kurs Satın Alma Akışı:**

```mermaid
sequenceDiagram
    participant Client
    participant Dispatcher
    participant CourseService
    participant MongoDB

    Client->>Dispatcher: POST /course/courses/{id}/purchase (Bearer Token)
    Dispatcher->>Dispatcher: Token doğrula (student rolü)
    Dispatcher->>Dispatcher: Yetki kontrol
    Dispatcher->>CourseService: POST /courses/{id}/purchase
    CourseService->>MongoDB: Kurs var mı? Aktif mi?
    MongoDB-->>CourseService: Kurs bilgisi
    CourseService->>MongoDB: Satın alma kaydet
    MongoDB-->>CourseService: OK
    CourseService-->>Dispatcher: 201 Satın alma başarılı
    Dispatcher-->>Client: 201 Created
```

**Karmaşıklık Analizi:**

| İşlem | Zaman Karmaşıklığı | Açıklama |
|-------|-------------------|----------|
| Token doğrulama | O(1) | JWT decode sabit süre |
| Yetki kontrolü | O(n) | n = permission kuralı sayısı |
| Kurs listeleme | O(n) | n = kurs sayısı |
| Kullanıcı arama | O(log n) | MongoDB index ile |

---

## 3. Sistem Mimarisi

### 3.1 Genel Mimari

```mermaid
flowchart TD
    Client([İstemci / Frontend])

    subgraph External["Dış Dünya (Port 8000)"]
        Dispatcher[Dispatcher / API Gateway]
    end

    subgraph Internal["İç Ağ (Docker Internal Network)"]
        Auth[Auth Service :8001]
        Course[Course Service :8000]
        Exam[Exam Service :8000]

        AuthDB[(Auth MongoDB)]
        CourseDB[(Course MongoDB)]
        ExamDB[(Exam MongoDB)]
        DispatcherDB[(Dispatcher MongoDB)]

        Prometheus[Prometheus :9090]
        Grafana[Grafana :3000]
        MongoExporter[MongoDB Exporter :9216]
    end

    Client --> Dispatcher
    Dispatcher --> Auth
    Dispatcher --> Course
    Dispatcher --> Exam
    Dispatcher --> DispatcherDB

    Auth --> AuthDB
    Course --> CourseDB
    Exam --> ExamDB

    MongoExporter --> DispatcherDB
    Prometheus --> MongoExporter
    Prometheus --> Dispatcher
    Grafana --> Prometheus
```

### 3.2 Network İzolasyonu

Mikroservisler dış dünyaya kapalıdır. Yalnızca Dispatcher `ports` ile dışarıya açılmış, diğer servisler `expose` ile sadece iç ağa açılmıştır.

```yaml
dispatcher:
  ports:
    - "8000:8000"   # Dışarıya açık

auth-service:
  expose:
    - "8001"        # Sadece iç ağa açık

course-service:
  expose:
    - "8000"        # Sadece iç ağa açık
```

**Network İzolasyonu Kanıtı:**

Aşağıdaki ekran görüntüleri, mikroservislere dışarıdan doğrudan erişimin engellendiğini kanıtlamaktadır:

❌ **Direkt erişim denemesi — BAŞARISIZ (port dışarıya kapalı):**

<img width="694" height="144" alt="Network isolation-1" src="https://github.com/user-attachments/assets/41c7ff44-2cab-46e3-84e5-92dcc21e9994" />


✅ **Dispatcher üzerinden erişim — BAŞARILI:**

<img width="1310" height="52" alt="Network isolation-2" src="https://github.com/user-attachments/assets/ad1ad445-e065-4a32-a049-1e1334af3f7b" />


### 3.3 Dispatcher Akış Diyagramı

```mermaid
flowchart TD
    A[İstek Geldi] --> B{Token var mı?}
    B -->|Hayır| C[401 Unauthorized]
    B -->|Evet| D{Token geçerli mi?}
    D -->|Hayır| E[401 Unauthorized]
    D -->|Evet| F{Yetki var mı?}
    F -->|Hayır| G[403 Forbidden]
    F -->|Evet| H{Servis müsait mi?}
    H -->|Timeout| I[504 Gateway Timeout]
    H -->|Bağlantı yok| J[503 Service Unavailable]
    H -->|Evet| K[İsteği İlet]
    K --> L{Servis yanıtı}
    L -->|Hata body| M[500 Internal Error]
    L -->|Normal| N[Yanıtı İlet]

    K --> O[(Dispatcher MongoDB\ntraffic_logs)]
```

### 3.4 TDD Yaklaşımı

Dispatcher servisi TDD (Red-Green-Refactor) metodolojisiyle geliştirilmiştir. Test dosyalarının commit zaman damgası, fonksiyonel kodlardan öncedir.

```mermaid
flowchart LR
    A["🔴 RED\nTest Yaz\nBaşarısız"] --> B["🟢 GREEN\nKodu Yaz\nTesti Geç"]
    B --> C["🔵 REFACTOR\nKodu İyileştir"]
    C --> A
```

**Test Kapsamı (Dispatcher):**

| Test No | Senaryo | Beklenen |
|---------|---------|----------|
| 1 | Başarılı yönlendirme | 200 OK |
| 2 | Token yok | 401 |
| 3 | Token bozuk | 401 |
| 4 | Yetkisiz rol | 403 |
| 5 | Servis hatası | 500 |
| 6 | Servis ölü | 503 |
| 7 | Timeout | 504 |
| 8-19 | Diğer senaryolar | Çeşitli |

### 3.5 Veritabanı E-R Diyagramı

```mermaid
erDiagram
    USERS {
        string username PK
        string hashed_password
        string role
    }

    COURSES {
        string id PK
        string title
        string level
        float price
        bool is_active
    }

    PURCHASES {
        string id PK
        string username FK
        string course_id FK
    }

    CART {
        string id PK
        string username FK
        array items
    }

    EXAMS {
        string id PK
        string title
        int duration_minutes
        bool is_active
    }

    SESSIONS {
        string id PK
        string username FK
        string exam_id FK
        datetime started_at
        bool submitted
        int score
    }

    PERMISSIONS {
        string id PK
        string service
        string method
        array allowed_roles
    }

    TRAFFIC_LOGS {
        string id PK
        string method
        string path
        int status_code
        datetime timestamp
    }

    USERS ||--o{ PURCHASES : yapar
    COURSES ||--o{ PURCHASES : içerir
    USERS ||--o{ CART : sahip
    USERS ||--o{ SESSIONS : girer
    EXAMS ||--o{ SESSIONS : içerir
```

---

## 4. API Endpoint Tabloları

### Auth Service

| Method | Endpoint | Açıklama | Rol |
|--------|----------|----------|-----|
| POST | /auth/register | Kayıt ol | Herkese açık |
| POST | /auth/login | Giriş yap | Herkese açık |
| GET | /auth/verify | Token doğrula | Herkese açık |
| GET | /auth/users | Kullanıcı listele | Admin |
| GET | /auth/user/{username} | Kullanıcı getir | Admin |
| PUT | /auth/user/{username} | Şifre güncelle | Admin/Kendisi |
| DELETE | /auth/user/{username} | Kullanıcı sil | Admin |

### Course Service

| Method | Endpoint | Açıklama | Rol |
|--------|----------|----------|-----|
| GET | /course/courses | Kurs listele | Herkes |
| GET | /course/courses/{id} | Kurs getir | Herkes |
| POST | /course/courses | Kurs oluştur | Teacher/Admin |
| PUT | /course/courses/{id} | Kurs güncelle | Teacher/Admin |
| DELETE | /course/courses/{id} | Kurs sil | Teacher/Admin |
| POST | /course/courses/{id}/purchase | Kurs satın al | Student |
| GET | /course/courses/my-purchases | Satın alınanlar | Student |
| POST | /course/courses/cart/add | Sepete ekle | Student |
| GET | /course/courses/cart | Sepet görüntüle | Student |
| DELETE | /course/courses/cart/{id} | Sepetten çıkar | Student |
| POST | /course/courses/cart/checkout | Sepeti satın al | Student |

### Exam Service

| Method | Endpoint | Açıklama | Rol |
|--------|----------|----------|-----|
| GET | /exam/exams | Sınav listele | Herkes |
| GET | /exam/exams/{id} | Sınav getir | Herkes |
| POST | /exam/exams | Sınav oluştur | Teacher/Admin |
| POST | /exam/exams/{id}/start | Sınava gir | Student |
| POST | /exam/exams/{id}/answer | Cevap kaydet | Student |
| POST | /exam/exams/{id}/submit | Sınavı bitir | Student |
| GET | /exam/exams/{id}/result/{username} | Sonuç gör | Herkes |

---

## 5. Kurulum ve Çalıştırma

```bash
# Repoyu klonla
git clone https://github.com/BiraliNesbuik/Academy-Microservices-Architectures.git

# Proje dizinine gir
cd Academy-Microservices-Architectures

# Tüm sistemi ayağa kaldır
docker-compose up --build
```

**Erişim Noktaları:**

| Servis | URL |
|--------|-----|
| API Gateway | http://localhost:8000 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| Frontend | http://localhost:5173 |

---

## 6. Test Sonuçları

### 6.1 Birim Testleri (Pytest)

Dispatcher servisi 19 test ile TDD yaklaşımıyla geliştirilmiştir.

```
tests/test_dispatcher.py - 19 passed
tests/test_course.py     - 14 passed
tests/test_auth.py       - 8 passed
```

### 6.2 Yük Testi Sonuçları (Locust)

| Kullanıcı Sayısı | Medyan Yanıt (ms) | 95. Persentil (ms) | Hata Oranı | RPS |
|-----------------|-------------------|-------------------|------------|-----|
| 50 | 800 | 3200 | %1 | 18.2 |
| 100 | 3100 | 9300 | %3 | 22.1 |
| 200 | 8100 | 30000 | %11 | 20.0 |

#### 50 Kullanıcı Testi

Chart <img width="1537" height="938" alt="50 kullanıcı charts" src="https://github.com/user-attachments/assets/877f3a86-7262-49ed-98c8-ea21e92c6f75" />


Statistics(<img width="1913" height="962" alt="50 kullanıcı statistics" src="https://github.com/user-attachments/assets/75615972-0ff2-49a9-b2c4-65484ad5d754" />


#### 100 Kullanıcı Testi

Charts <img width="1551" height="937" alt="100 kullanıcı charts" src="https://github.com/user-attachments/assets/38d9eb0c-7b84-4cad-a75f-84efe89d6a94" />


Statistics <img width="1917" height="945" alt="100 kullanıcı statistics" src="https://github.com/user-attachments/assets/db1732dd-5ad3-4d12-be91-ecba5cbf4f11" />


#### 200 Kullanıcı Testi

Charts <img width="1529" height="939" alt="chart" src="https://github.com/user-attachments/assets/ec1accb4-de4d-4a5b-844c-92969c1e425f" />


Statistics <img width="1919" height="959" alt="statistics" src="https://github.com/user-attachments/assets/c519cc0c-7eb4-45fb-a260-3db452510084" />


### 6.3 Grafana Monitoring

Dispatcher trafiği Prometheus + Grafana ile izlenmektedir. `prometheus-fastapi-instrumentator` kütüphanesi kullanılarak `/metrics` endpoint'i otomatik olarak oluşturulmuştur.

**İzlenen Metrikler:**
- `http_requests_total` — endpoint bazlı toplam istek sayısı
- `http_request_duration_seconds` — yanıt süreleri
- `mongodb_up` — MongoDB sağlık durumu

**Yanıt Süresi Grafiği:**

Yanit Suresi Grafigi <img width="1537" height="814" alt="Yanıt süresi grafiği" src="https://github.com/user-attachments/assets/f8de501b-9045-428d-a770-805b2f05d7f2" />


**Yük Testi ve Trafik Hacmi:**

Yuk Testi ve Trafik Hacmi <img width="1521" height="760" alt="Yük testi ve trafik hacmi" src="https://github.com/user-attachments/assets/27e5d353-595d-4f5a-a4b0-a8433fd99ad8" />


**Trafik Log Tabloları:**

Trafik Log Tablosu 1 <img width="1523" height="742" alt="Tablo 1" src="https://github.com/user-attachments/assets/aa0b462b-c319-4eed-935e-10e3415e8f7d" />


Trafik Log Tablosu 2 <img width="1518" height="742" alt="Tablo 2" src="https://github.com/user-attachments/assets/4dc4d2da-034c-4e58-8a29-801aa788d5a1" />


---

## 7. Sonuç ve Tartışma

### Başarılar
- Mikroservis mimarisi başarıyla implemente edilmiştir
- Dispatcher TDD ile geliştirilmiş, 19 test geçmektedir
- Network isolation Docker iç ağı ile sağlanmıştır
- Grafana + Prometheus ile gerçek zamanlı monitoring kurulmuştur
- Role-based access control (RBAC) uygulanmıştır
- Sepet özelliği ile çoklu kurs satın alma desteklenmektedir
- React frontend ile kullanıcı dostu arayüz geliştirilmiştir

### Sınırlılıklar
- Sınav modülünde süre kontrolü frontend tarafında yapılamamıştır
- Servisler arası doğrudan iletişim yoktur, tüm trafik dispatcher üzerinden geçer
- Ödeme sistemi entegre edilmemiştir
- Token yenileme (refresh token) mekanizması bulunmamaktadır

### Olası Geliştirmeler
- Gerçek ödeme gateway entegrasyonu (Stripe, iyzico)
- Sınav süresi otomatik sayacı ve otomatik submit
- Bildirim servisi (email/SMS)
- Cache katmanı (Redis) ile performans artışı
- CI/CD pipeline kurulumu
- Kubernetes ile container orchestration
