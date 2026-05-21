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

- FastAPI — inference API и Swagger UI
- Airflow — orchestration batch pipeline
- Docker — контейнеризация
- MinIO — S3-хранилище артефактов
- RandomForestRegressor — ML модель
- Pandas / Scikit-learn — обработка и ML
- S3 artifact versioning через execution_date и run_id

---

# ⚙️ Pipeline

DAG `warehouse_batch_pipeline` выполняет:

1. `check_idempotency`
2. `load_data`
3. `preprocess_data`
4. `run_ml_pipeline`
5. `run_inference`
6. `upload_to_minio`
7. `backfill_task`

Каждый stage pipeline запускается как отдельный Docker container через Airflow DockerOperator.

Pipeline поддерживает:
- batch processing
- scheduled execution
- dynamic inference
- artifact versioning
- idempotent reruns
- historical backfill
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


# 🔮 Dynamic Inference

Система поддерживает динамический inference pipeline.

Пользователь может:

- загрузить новый файл остатков через FastAPI
- автоматически выполнить inference
- получить рекомендации по закупкам
- сохранить историю inference
- сохранить результаты в MinIO
- сохранить historical inference artifacts

Inference pipeline включает:

- загрузку модели
- feature engineering
- прогнозирование спроса
- расчёт recommended_order
- расчёт critical_order
- upload результатов в S3/MinIO

История inference сохраняется отдельно для каждой даты и DAG run.

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
MINIO_ROOT_USER=ваш логин
MINIO_ROOT_PASSWORD=ваш пароль

S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=ваш логин
S3_SECRET_KEY=ваш пароль
S3_BUCKET=warehouse-ml

AIRFLOW_USERNAME=ваш логин
AIRFLOW_PASSWORD=ваш пароль
AIRFLOW_FIRSTNAME=FIRSTNAME
AIRFLOW_LASTNAME=LASTNAME
AIRFLOW_EMAIL=your_email@mail.com
```

---

# 🐳 Сборка Docker image

```bash
docker build -t warehouse-ml-app:latest .
```

---

# 🚀 Запуск сервисов

Перед запуском убедитесь, что Docker Desktop запущен.

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
ваш логин
```

Пароль:

```text
ваш пароль
```

---

## MinIO

```text
http://localhost:9001
```

Логин:

```text
ваш логин
```

Пароль:

```text
ваш пароль
```

---

---

# 🌍 Remote Access

Проект поддерживает удалённый доступ через Tailscale.

Это позволяет:

- открывать Swagger UI с другого устройства
- использовать Airflow удалённо
- просматривать MinIO через интернет
- демонстрировать систему без переноса проекта

Примеры:

```text
http://100.x.x.x:8000/docs
http://100.x.x.x:8080
http://100.x.x.x:9001
```

# ▶ Запуск DAG

1. Открыть Airflow
2. Включить DAG `warehouse_batch_pipeline`
3. Нажать `Trigger DAG`

---

# 📦 Результаты pipeline

После выполнения DAG:

- обучается ML модель
- выполняется inference
- формируются рекомендации
- сохраняется inference history
- артефакты загружаются в MinIO

Структура в S3:

```text
models/
  2024-01-01/
    scheduled__run_id/
      model.pkl

recommendations/
  latest_recommendations.csv

recommendations/history/
  2024-01-01/
    scheduled__run_id/
      inference_recommendations.csv

datasets/inference_history/
  2024-01-01/
    scheduled__run_id/
      inference_history.csv
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

# 🔄 Inference Flow

1. Пользователь загружает новый stock файл
2. FastAPI сохраняет файл
3. Загружается обученная модель
4. Выполняется feature engineering
5. Выполняется ML inference
6. Формируются рекомендации
7. Результаты сохраняются локально
8. Артефакты загружаются в MinIO
9. История inference сохраняется отдельно


# 📡 API

FastAPI используется для:

- загрузки новых stock файлов
- запуска inference
- получения последних рекомендаций
- получения JSON результатов
- интеграции с внешними системами

Запуск API:

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

Swagger UI:

```text
http://localhost:8000/docs
```

Основные endpoints:

| Endpoint | Description |
|---|---|
| `/upload-stock-and-inference` | upload stock file and run inference |
| `/recommendations/latest` | get latest recommendations CSV |
| `/recommendations/latest-json` | get latest recommendations JSON |

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