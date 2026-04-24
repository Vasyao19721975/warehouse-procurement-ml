from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount


default_args = {
    "owner": "mikhail",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="warehouse_batch_pipeline",
    default_args=default_args,
    description="Batch ML pipeline for warehouse procurement recommendations",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=True,
    max_active_runs=1,
    tags=["ml", "batch", "warehouse"],
) as dag:

    run_pipeline = DockerOperator(
        task_id="run_ml_pipeline",
        image="warehouse-ml-app:latest",
        command="python -m src.main",
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
        mounts=[
            Mount(
                source="C:/Жеский диплом/diploma_warehouse_project",
                target="/app",
                type="bind",
            )
        ],
        working_dir="/app",
        mount_tmp_dir=False,
        auto_remove=True,
    )

    run_pipeline