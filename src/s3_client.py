import boto3
from botocore.client import Config

from src.config import (
    S3_ENDPOINT,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    S3_BUCKET,
    RUN_DATE,
    RUN_ID,
)


s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)


def create_bucket_if_not_exists():
    existing_buckets = s3_client.list_buckets()

    bucket_names = [
        bucket["Name"]
        for bucket in existing_buckets.get("Buckets", [])
    ]

    if S3_BUCKET not in bucket_names:
        s3_client.create_bucket(Bucket=S3_BUCKET)
        print(f"Bucket created: {S3_BUCKET}")
    else:
        print(f"Bucket already exists: {S3_BUCKET}")


def upload_file(local_path: str, object_name: str):
    s3_client.upload_file(
        local_path,
        S3_BUCKET,
        object_name,
    )

    print(f"Uploaded: {object_name}")


def upload_artifacts(model_path: str, output_path: str):
    safe_run_id = (
        RUN_ID.replace(":", "_")
        .replace("+", "_")
        .replace("/", "_")
        .replace(" ", "_")
    )

    model_object_name = f"models/{RUN_DATE}/{safe_run_id}/model.pkl"
    output_object_name = f"outputs/{RUN_DATE}/{safe_run_id}/final_recommendations.csv"

    create_bucket_if_not_exists()

    upload_file(model_path, model_object_name)
    upload_file(output_path, output_object_name)

    print("Artifacts uploaded to MinIO:")
    print(f"Model: {model_object_name}")
    print(f"Output: {output_object_name}")
    
def upload_inference_artifacts(
    recommendations_path: str,
    history_path: str,
    recommendation_date: str,
):
    safe_run_id = (
        RUN_ID.replace(":", "_")
        .replace("+", "_")
        .replace("/", "_")
        .replace(" ", "_")
    )

    latest_object_name = "recommendations/latest_recommendations.csv"

    history_recommendation_object_name = (
        f"recommendations/history/{recommendation_date}/{safe_run_id}/"
        f"inference_recommendations.csv"
    )

    history_state_object_name = (
        f"datasets/inference_history/{recommendation_date}/{safe_run_id}/"
        f"inference_history.csv"
    )

    create_bucket_if_not_exists()

    upload_file(recommendations_path, latest_object_name)
    upload_file(recommendations_path, history_recommendation_object_name)
    upload_file(history_path, history_state_object_name)

    print("Inference artifacts uploaded to MinIO:")
    print(f"Latest recommendations: {latest_object_name}")
    print(f"Historical recommendations: {history_recommendation_object_name}")
    print(f"Inference history: {history_state_object_name}")