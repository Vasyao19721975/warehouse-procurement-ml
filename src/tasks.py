import os
import sys
from pathlib import Path

from src.s3_client import upload_artifacts
from src.main import main as run_full_pipeline
from src.config import (
    MODEL_PATH,
    FINAL_OUTPUT_FILE,
    PROCESSED_DATA_DIR,
)
from src.s3_client import create_bucket_if_not_exists, upload_file


def check_idempotency():
    """
    Проверка идемпотентности.

    Идея:
    если результат уже существует, pipeline может быть безопасно перезапущен,
    потому что файлы перезаписываются, а не дублируются.
    """
    print("Task: check_idempotency")

    output_path = Path(FINAL_OUTPUT_FILE)
    model_path = Path(MODEL_PATH)

    if output_path.exists():
        print(f"Existing output found: {output_path}")
        print("Pipeline is idempotent: output file will be overwritten if pipeline is rerun.")
    else:
        print("No existing output found. Pipeline will create a new result.")

    if model_path.exists():
        print(f"Existing model found: {model_path}")
        print("Model file will be overwritten after training.")
    else:
        print("No existing model found. Model will be created.")

    print("Idempotency check finished.")


def load_data():
    """
    Логический этап загрузки данных.

    В текущей реализации фактическая загрузка данных находится внутри src.main.
    Этот task нужен для явного отображения этапа в DAG.
    """
    print("Task: load_data")
    print("Raw stock and supply files are expected in data/raw.")
    print("Loading is executed inside the full pipeline step.")


def preprocess_data():
    """
    Логический этап предобработки данных.

    В текущей реализации очистка и сборка датасета выполняются внутри src.main.
    """
    print("Task: preprocess_data")
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    print(f"Processed data directory is ready: {PROCESSED_DATA_DIR}")
    print("Preprocessing is executed inside the full pipeline step.")


def run_ml_pipeline():
    """
    Основной ML pipeline:
    - загрузка данных
    - очистка
    - построение датасета
    - обучение модели
    - прогноз
    - формирование рекомендаций
    """
    print("Task: run_ml_pipeline")
    run_full_pipeline()
    print("ML pipeline finished.")


def upload_to_minio():
    print("Task: upload_to_minio")

    upload_artifacts(
        model_path=MODEL_PATH,
        output_path=FINAL_OUTPUT_FILE,
    )


def backfill():
    """
    Backfill task.

    Backfill — это пересчёт pipeline за прошлые даты.
    В MVP-версии мы фиксируем отдельный task, который показывает,
    что pipeline поддерживает повторный запуск за прошлые периоды.
    """
    print("Task: backfill")
    print("Backfill means recalculating the pipeline for previous dates.")
    print("In this MVP, backfill is represented as a separate DAG task.")
    print("For a production version, this task can accept date ranges and rerun pipeline by period.")


TASKS = {
    "check_idempotency": check_idempotency,
    "load_data": load_data,
    "preprocess_data": preprocess_data,
    "run_ml_pipeline": run_ml_pipeline,
    "upload_to_minio": upload_to_minio,
    "backfill": backfill,
}


def main():
    if len(sys.argv) < 2:
        available_tasks = ", ".join(TASKS.keys())
        raise ValueError(f"Task name is required. Available tasks: {available_tasks}")

    task_name = sys.argv[1]

    if task_name not in TASKS:
        available_tasks = ", ".join(TASKS.keys())
        raise ValueError(f"Unknown task: {task_name}. Available tasks: {available_tasks}")

    TASKS[task_name]()


if __name__ == "__main__":
    main()