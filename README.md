# Warehouse Procurement ML

ML-сервис для автоматизации закупок на складе с использованием анализа данных, прогнозирования спроса и batch orchestration через Airflow.

---

# 📌 Возможности проекта

Система:

- анализирует остатки и поставки
- рассчитывает продажи
- прогнозирует спрос
- формирует рекомендации по закупкам
- обучает ML-модель
- сохраняет артефакты в MinIO (S3)
- поддерживает batch pipeline через Airflow
- поддерживает backfill и идемпотентность

---

# 🏗 Архитектура

Проект состоит из:

- FastAPI — API сервиса
- Airflow — orchestration batch pipeline
- Docker — контейнеризация
- MinIO — S3-хранилище артефактов
- RandomForestRegressor — ML модель
- Pandas / Scikit-learn — обработка и ML

---

# ⚙️ Pipeline

DAG `warehouse_batch_pipeline` выполняет:

1. `check_idempotency`
2. `load_data`
3. `preprocess_data`
4. `run_ml_pipeline`
5. `upload_to_minio`
6. `backfill_task`

---

# 🧠 ML модель

Используется:

- `RandomForestRegressor`

Фичи:

- `lag_1`
- `lag_2`
- historical sales
- stock
- supply
- days_of_stock

Метрика:

- `MAE (Mean Absolute Error)`

---

# 📁 Структура проекта

```text
warehouse-procurement-ml/
│
├── dags/                     # Airflow DAG
├── data/                     # Данные
├── models/                   # ML модели
├── notebooks/                # Jupyter notebooks
├── outputs/                  # Результаты pipeline
├── src/                      # Исходный код
├── tests/                    # Тесты
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
├── ML_SYSTEM_DESIGN.md
└── ARCHITECTURE.md
```

---

# 🚀 Полное развёртывание проекта

## 1. Клонирование репозитория

```bash
git clone <YOUR_REPOSITORY_URL>
cd warehouse-procurement-ml
```

---

# 🐳 Установка Docker

Установить:

- Docker Desktop

Проверка:

```bash
docker --version
docker compose version
```

---

# 🐍 Установка Python

Требуется:

- Python 3.10+

Проверка:

```bash
python --version
```

---

# 📦 Установка зависимостей

```bash
pip install -r requirements.txt
```

---

# 🔐 Создание `.env`

В корне проекта создать файл:

```text
.env
```

Содержимое:

```env
MINIO_ROOT_USER=vasyao
MINIO_ROOT_PASSWORD=prpup123

S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=vasyao
S3_SECRET_KEY=prpup123
S3_BUCKET=warehouse-ml

AIRFLOW_USERNAME=vasyao
AIRFLOW_PASSWORD=prpup123
AIRFLOW_FIRSTNAME=Mikhail
AIRFLOW_LASTNAME=Belkin
AIRFLOW_EMAIL=your_email@mail.com
```

---

# 🐳 Сборка Docker image

```bash
docker build -t warehouse-ml-app:latest .
```

---

# 🚀 Запуск сервисов

```bash
docker compose up -d
```

Проверка контейнеров:

```bash
docker ps
```

---

# 🌐 Интерфейсы сервисов

## Airflow

```text
http://localhost:8080
```

Логин:

```text
vasyao
```

Пароль:

```text
prpup123
```

---

## MinIO

```text
http://localhost:9001
```

Логин:

```text
vasyao
```

Пароль:

```text
prpup123
```

---

# ▶ Запуск DAG

1. Открыть Airflow
2. Включить DAG `warehouse_batch_pipeline`
3. Нажать `Trigger DAG`

---

# 📦 Результаты pipeline

После выполнения DAG:

- обучается ML модель
- формируются рекомендации
- артефакты загружаются в MinIO

Структура в S3:

```text
outputs/
  2024-01-01/
    scheduled__2024-01-01T00_00_00+00_00/
      final_recommendations.csv

models/
  2024-01-01/
    scheduled__2024-01-01T00_00_00+00_00/
      model.pkl
```

---

# 🔁 Backfill и идемпотентность

Pipeline поддерживает:

- backfill за прошлые даты
- повторные DAG runs
- сохранение старых артефактов
- отсутствие перезаписи предыдущих результатов

Каждый запуск DAG сохраняется отдельно через `run_id`.

---

# 🧪 Запуск тестов

```bash
pytest
```

Покрытие:

```bash
pytest --cov=src tests/
```

---

# 📡 API

Запуск API:

```bash
uvicorn src.api:app --reload
```

Swagger UI:

```text
http://localhost:8000/docs
```

---

# 📊 Используемые технологии

- Python
- Pandas
- Scikit-learn
- FastAPI
- Airflow
- Docker
- MinIO
- Pytest
- Boto3

---

# 👨‍💻 Автор

Mikhail Belkin

---

# 📄 Документация

- `ML_SYSTEM_DESIGN.md`
- `ARCHITECTURE.md`