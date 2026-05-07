# Architecture

## 1. General Approach

Система реализована как batch-пайплайн для регулярного пересчёта рекомендаций по закупке товаров.

Основной сценарий работы:
1. загрузка данных об остатках и поставках;
2. предобработка данных;
3. расчёт продаж;
4. построение baseline-рекомендаций;
5. обучение ML-модели;
6. прогнозирование спроса;
7. формирование итоговых рекомендаций;
8. сохранение результатов.

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
outputs/<execution_date>/<run_id>/
models/<execution_date>/<run_id>/
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

## 7. Idempotency

Pipeline поддерживает идемпотентность на уровне S3/MinIO storage.

Особенности реализации:

- каждый DAG run сохраняется отдельно;
- результаты не перезаписывают предыдущие артефакты;
- поддерживается backfill за прошлые даты;
- структура хранения разделена по execution date и run_id;
- повторный запуск DAG создаёт новую директорию.

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

## 8. Scalability

Система масштабируется за счёт:

- увеличения объёма данных;
- добавления новых признаков;
- замены модели;
- перехода к оркестратору (Airflow);
- переноса хранения в централизованные системы.

---

## 9. Risks and Limitations

Ограничения:

- локальный запуск;
- нет scheduler в базовой версии;
- нет model registry;
- ограниченные признаки;
- нет online-инференса.

---

## 10. Future Improvements

- переход к near real-time;
- API сервис;
- мониторинг модели;
- автоматическое переобучение;

- migration to distributed storage;
- model registry;
- CI/CD pipeline;
- Kubernetes deployment.

## 11. Orchestration

Для orchestration pipeline используется Apache Airflow.

Каждый этап pipeline запускается как отдельный Docker-based task через DockerOperator.

Это обеспечивает:
- изоляцию этапов;
- воспроизводимость окружения;
- независимый запуск задач;
- удобный monitoring DAG execution.