from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount


default_args = {
    "owner": "mikhail",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


PROJECT_PATH = "C:/Жеский диплом/diploma_warehouse_project"


with DAG(
    dag_id="warehouse_batch_pipeline",
    default_args=default_args,
    description="Warehouse ML batch pipeline with MinIO and DockerOperator",
    start_date=datetime(2026, 5, 1),
    schedule_interval="@daily",
    catchup=True,
    max_active_runs=1,
    tags=["ml", "warehouse", "batch"],
) as dag:

    common_kwargs = {
    "image": "warehouse-ml-app:latest",
    "docker_url": "unix://var/run/docker.sock",
    "network_mode": "diploma_warehouse_project_default",
    "mount_tmp_dir": False,
    "auto_remove": True,
    "working_dir": "/app",
    "environment": {
    "S3_ENDPOINT": os.getenv("S3_ENDPOINT"),
    "S3_ACCESS_KEY": os.getenv("S3_ACCESS_KEY"),
    "S3_SECRET_KEY": os.getenv("S3_SECRET_KEY"),
    "S3_BUCKET": os.getenv("S3_BUCKET"),
    "RUN_DATE": "{{ ds }}",
    "RUN_ID": "{{ run_id }}",
    },
    "mounts": [
        Mount(
            source=PROJECT_PATH,
            target="/app",
            type="bind",
        )
    ],
}

    check_idempotency = DockerOperator(
        task_id="check_idempotency",
        command="python -m src.tasks check_idempotency",
        **common_kwargs,
    )

    load_data = DockerOperator(
        task_id="load_data",
        command="python -m src.tasks load_data",
        **common_kwargs,
    )

    preprocess_data = DockerOperator(
        task_id="preprocess_data",
        command="python -m src.tasks preprocess_data",
        **common_kwargs,
    )

    run_ml_pipeline = DockerOperator(
        task_id="run_ml_pipeline",
        command="python -m src.tasks run_ml_pipeline",
        **common_kwargs,
    )

    upload_to_minio = DockerOperator(
        task_id="upload_to_minio",
        command="python -m src.tasks upload_to_minio",
        **common_kwargs,
    )

    backfill_task = DockerOperator(
        task_id="backfill_task",
        command="python -m src.tasks backfill",
        **common_kwargs,
    )

    (
        check_idempotency
        >> load_data
        >> preprocess_data
        >> run_ml_pipeline
        >> upload_to_minio
        >> backfill_task
    )