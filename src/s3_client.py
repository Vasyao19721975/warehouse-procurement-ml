import boto3
from botocore.client import Config

from src.config import (
    S3_ENDPOINT,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    S3_BUCKET,
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