"""Copy configured upload objects into a separate private S3-compatible bucket.

Schedule with separate BACKUP_S3_* credentials. Matching SHA-256 metadata is
skipped, so repeated runs only upload new or changed objects.
"""

from __future__ import annotations

import hashlib
import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from backend.app.core.config import settings


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def make_client(endpoint_url: str | None, region: str, access_key: str, secret_key: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url or None,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def main() -> None:
    if settings.file_storage_backend != "s3":
        raise SystemExit("FILE_STORAGE_BACKEND must be s3 to back up object uploads.")

    source = make_client(
        settings.s3_endpoint_url,
        settings.s3_region,
        settings.s3_access_key_id or "",
        settings.s3_secret_access_key or "",
    )
    destination = make_client(
        os.environ.get("BACKUP_S3_ENDPOINT_URL", ""),
        os.environ.get("BACKUP_S3_REGION", "auto"),
        required_env("BACKUP_S3_ACCESS_KEY_ID"),
        required_env("BACKUP_S3_SECRET_ACCESS_KEY"),
    )
    backup_bucket = required_env("BACKUP_S3_BUCKET")
    backup_endpoint = os.environ.get("BACKUP_S3_ENDPOINT_URL", "").rstrip("/")
    source_endpoint = (settings.s3_endpoint_url or "").rstrip("/")
    if backup_bucket == settings.s3_bucket and backup_endpoint == source_endpoint:
        raise SystemExit("Backup destination must be a different bucket or object-storage endpoint.")

    paginator = source.get_paginator("list_objects_v2")
    copied = 0
    unchanged = 0
    for page in paginator.paginate(Bucket=settings.s3_bucket):
        for item in page.get("Contents", []):
            key = item["Key"]
            response = source.get_object(Bucket=settings.s3_bucket, Key=key)
            body = response["Body"].read()
            sha256 = hashlib.sha256(body).hexdigest()

            try:
                current = destination.head_object(Bucket=backup_bucket, Key=key)
                if current.get("Metadata", {}).get("sha256") == sha256:
                    unchanged += 1
                    continue
            except ClientError as exc:
                status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
                if status != 404:
                    raise

            put_args = {
                "Bucket": backup_bucket,
                "Key": key,
                "Body": body,
                "Metadata": {"sha256": sha256},
            }
            if response.get("ContentType"):
                put_args["ContentType"] = response["ContentType"]
            destination.put_object(**put_args)
            copied += 1

    print(f"Backup complete: {copied} copied, {unchanged} unchanged.")


if __name__ == "__main__":
    main()
