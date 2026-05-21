# Architecture

## 1. General Approach

Система реализована как ML-based batch и inference pipeline для автоматизации закупок товаров на складе.

Архитектура объединяет:

- batch training pipeline;
- dynamic inference pipeline;
- REST API;
- orchestration через Airflow;
- хранение артефактов в MinIO (S3-compatible storage).

Основные сценарии работы:

### Batch pipeline
1. загрузка данных;
2. предобработка;
3. расчёт продаж;
4. обучение модели;
5. inference;
6. сохранение артефактов;
7. сохранение history.

### API inference pipeline
1. загрузка нового stock файла через FastAPI;
2. запуск inference;
3. генерация рекомендаций;
4. upload результатов в MinIO;
5. сохранение inference history.

---

## 2. Pipeline Stages

### Stage 1. Data Ingestion
На этом этапе система считывает сырые данные из файлов:
- остатки товаров;
- поставки товаров.

### Stage 2. Data Preprocessing
Данные очищаются, приводятся к нужным типам и агрегируются по SKU и дате.

### Stage 3. Sales Calculation
На основе изменения остатков и поставок рассчитываются продажи по каждому товару.

### Stage 4. Baseline Recommendation
На основе средней скорости продаж вычисляются:
- sales_per_day
- days_of_stock
- recommended_order
- decision

### Stage 5. ML Training
На подготовленных исторических данных формируются признаки:
- lag_1
- lag_2

После этого обучается модель RandomForestRegressor.

### Stage 6. Prediction
Модель прогнозирует спрос для каждого SKU.

### Stage 7. Final Recommendation
На основе прогноза спроса рассчитываются:
- predicted_sales
- ml_recommended_order
- difference между baseline и ML-подходом

### Stage 8. Output Saving
Результат сохраняется в итоговый файл:
- `outputs/final_recommendations.csv`

### Stage 9. API Inference

FastAPI позволяет запускать inference через HTTP API.

Основные возможности:
- upload нового stock файла;
- запуск inference pipeline;
- получение рекомендаций;
- получение JSON результатов;
- удалённый доступ через Swagger UI.

API используется как inference service layer.

---

## 3. Main Components

Основные компоненты системы:

- `load_data.py` — загрузка данных;
- `preprocess.py` — очистка и подготовка данных;
- `calculate_sales.py` — расчёт продаж;
- `recommendation_pipeline.py` — базовые рекомендации;
- `ml_pipeline.py` — обучение и прогнозирование;
- `main.py` — оркестрация полного пайплайна;
- `config.py` — централизованное хранение настроек и путей.
- `inference.py` — dynamic inference pipeline;
- `api.py` — FastAPI service layer;
- `tasks.py` — Airflow task execution layer;
- `warehouse_batch_dag.py` — Airflow DAG orchestration;
- `s3_client.py` — работа с MinIO/S3 storage;

---

## 4. Execution Model

Система запускается в batch-режиме.

Команда запуска:
```bash
python -m src.main
```

---

## 5. Storage

В текущей реализации используются следующие уровни хранения:

- `data/raw/` — сырые входные данные;
- `data/processed/` — промежуточные обработанные данные;
- `outputs/` — финальные рекомендации.

В production pipeline артефакты дополнительно сохраняются в MinIO (S3-compatible storage).

Используется следующая структура хранения:

```text
models/<execution_date>/<run_id>/
recommendations/history/<execution_date>/<run_id>/
datasets/inference_history/<execution_date>/<run_id>/
```

Это позволяет:
- хранить историю запусков;
- выполнять backfill;
- избегать перезаписи результатов;
- реализовать идемпотентный batch pipeline.

В production-сценарии данные и артефакты могут быть перенесены:

- в объектное хранилище (S3/MinIO);
- в базу данных;
- в хранилище артефактов модели.

---

## 6. Service Layer (Batch Service)

Система реализована как batch-сервис.

Airflow используется как orchestration layer для управления DAG pipeline и Docker-based tasks.

Pipeline может запускаться:
- вручную;
- по расписанию;
- через Airflow.

Основная команда:
```bash
python -m src.main
```
---


## 7. Remote Access

Для удалённого доступа используется Tailscale.

Это позволяет:
- открывать Swagger UI удалённо;
- использовать Airflow с другого устройства;
- подключаться к MinIO через интернет;
- демонстрировать систему без переноса проекта.

Поддерживается доступ к:
- FastAPI;
- Airflow;
- MinIO.

## 8. Idempotency

Pipeline поддерживает идемпотентность на уровне S3/MinIO storage.

Особенности реализации:

- latest artifacts обновляются при каждом запуске;
- historical artifacts сохраняются отдельно;
- каждый DAG run имеет собственный run_id;
- поддерживается backfill;
- поддерживается idempotent rerun;
- inference history сохраняется отдельно по execution date и run_id.

Пример структуры:

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

Такой подход обеспечивает:
- воспроизводимость результатов;
- хранение истории запусков;
- безопасный re-run pipeline;
- отсутствие потери предыдущих артефактов.

---

## 9. Scalability

Система масштабируется за счёт:

- увеличения объёма данных;
- добавления новых признаков;
- замены модели;
- перехода к оркестратору (Airflow);
- переноса хранения в централизованные системы.

---

## 10. Risks and Limitations

Ограничения:

- локальное развёртывание;
- ограниченный объём исторических данных;
- отсутствует model registry;
- отсутствует distributed execution;
- отсутствует monitoring production metrics.
---

## 11. Future Improvements

- переход к near real-time;
- API сервис;
- мониторинг модели;
- автоматическое переобучение;

- migration to distributed storage;
- model registry;
- CI/CD pipeline;
- Kubernetes deployment.

- asynchronous inference;
- message broker integration;
- streaming ingestion;
- GPU inference;
- distributed training;
- automatic model versioning;
- RBAC/security layer;

## 12. Orchestration

Для orchestration pipeline используется Apache Airflow.

Каждый этап pipeline запускается как отдельный Docker-based task через DockerOperator.

Это обеспечивает:
- изоляцию этапов;
- воспроизводимость окружения;
- независимый запуск задач;
- удобный monitoring DAG execution.

## 13. API Architecture

FastAPI используется как REST inference layer.

Основные endpoints:

- `/upload-stock-and-inference`
- `/recommendations/latest`
- `/recommendations/latest-json`

API поддерживает:
- file upload;
- inference execution;
- recommendation retrieval;
- Swagger documentation;
- remote access через Tailscale.