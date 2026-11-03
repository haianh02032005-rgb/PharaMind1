"""Private, configurable storage for uploaded prescription source files."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse

from backend.app.core.config import PROJECT_ROOT, settings


class PrescriptionFileStorage:
    """Write uploaded files to a persistent local volume or S3-compatible bucket."""

    def save(
        self,
        *,
        family_id: int,
        member_id: int,
        extension: str,
        content: bytes,
        content_type: str | None = None,
        sha256: str | None = None,
    ) -> str:
        key = self._object_key(family_id, member_id, extension)
        if settings.file_storage_backend == "s3":
            return self._save_s3(key, content, content_type, sha256)
        return self._save_local(key, content)

    def delete(self, location: str) -> None:
        """Delete a stored upload without allowing paths outside its storage root."""
        if location.startswith("s3://"):
            self._delete_s3(location)
            return
        self._delete_local(location)

    @staticmethod
    def _object_key(family_id: int, member_id: int, extension: str) -> str:
        prefix = settings.s3_prefix.strip(" /")
        parts = [part for part in (prefix, f"family_{family_id}", f"member_{member_id}") if part]
        return "/".join([*parts, f"{uuid.uuid4().hex}.{extension.lower()}"])

    @staticmethod
    def _save_local(key: str, content: bytes) -> str:
        configured_root = Path(settings.file_storage_local_path).expanduser()
        root = configured_root if configured_root.is_absolute() else PROJECT_ROOT / configured_root
        target = root / Path(key)
        target.parent.mkdir(parents=True, exist_ok=True)

        # A temp file plus atomic rename prevents a crash from leaving a partial upload.
        fd, temp_name = tempfile.mkstemp(prefix=".upload-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as temp_file:
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_name, target)
        except Exception:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
            raise
        return str(target)

    @staticmethod
    def _save_s3(
        key: str,
        content: bytes,
        content_type: str | None,
        sha256: str | None,
    ) -> str:
        # Imported only when S3 is selected so local-only installs need no SDK setup.
        import boto3
        from botocore.config import Config

        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        extra_args: dict[str, object] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if sha256:
            extra_args["Metadata"] = {"sha256": sha256}
        client.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=content,
            **extra_args,
        )
        # Retain a provider-neutral locator in import_sessions.storage_path.
        return f"s3://{settings.s3_bucket}/{key}"

    @staticmethod
    def _delete_local(location: str) -> None:
        configured_root = Path(settings.file_storage_local_path).expanduser()
        root = configured_root if configured_root.is_absolute() else PROJECT_ROOT / configured_root
        resolved_root = root.resolve()
        candidate = Path(location).expanduser()
        target = (candidate if candidate.is_absolute() else PROJECT_ROOT / candidate).resolve()

        try:
            target.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError("Refusing to delete a file outside FILE_STORAGE_LOCAL_PATH") from exc

        target.unlink(missing_ok=True)

    @staticmethod
    def _delete_s3(location: str) -> None:
        parsed = urlparse(location)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        if not bucket or not key:
            raise ValueError("Invalid S3 upload location")
        if bucket != settings.s3_bucket:
            raise ValueError("Refusing to delete an object outside the configured S3 bucket")

        import boto3
        from botocore.config import Config

        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        client.delete_object(Bucket=bucket, Key=key)
