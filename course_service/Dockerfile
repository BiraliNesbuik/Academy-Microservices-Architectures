FROM python:3.11-slim

WORKDIR /app

# Önce sadece bağımlılıkları kopyalayıp yükleyelim (Cache avantajı için)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Şimdi tüm kodları kopyalayalım
COPY . .

# Uygulamayı başlatalım
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]