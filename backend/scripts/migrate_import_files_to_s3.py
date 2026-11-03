"""Copy existing local import uploads to the configured S3-compatible bucket.

Run with FILE_STORAGE_BACKEND=s3 after configuring the bucket and database:
    python -m backend.scripts.migrate_import_files_to_s3
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import select

from backend.app.core.config import PROJECT_ROOT, settings
from backend.app.db.session import SessionLocal
from backend.app.models.import_session import ImportSession
from backend.app.modules.imports.file_storage import PrescriptionFileStorage


def main() -> None:
    if settings.file_storage_backend != "s3":
        raise SystemExit("Set FILE_STORAGE_BACKEND=s3 before migrating local uploads.")

    storage = PrescriptionFileStorage()
    migrated = 0
    missing = 0
    with SessionLocal() as db:
        sessions = db.scalars(select(ImportSession).order_by(ImportSession.id)).all()
        for session in sessions:
            old_location = session.storage_path
            if not old_location or old_location.startswith("s3://"):
                continue

            source = Path(old_location).expanduser()
            if not source.is_absolute():
                source = PROJECT_ROOT / source
            if not source.is_file():
                print(f"SKIP import #{session.id}: local file is missing ({source})")
                missing += 1
                continue

            content = source.read_bytes()
            new_location = storage.save(
                family_id=session.family_id,
                member_id=session.member_id,
                extension=source.suffix.lstrip(".") or "bin",
                content=content,
                content_type=session.mime_type,
                sha256=hashlib.sha256(content).hexdigest(),
            )
            session.storage_path = new_location
            db.commit()
            migrated += 1
            print(f"MIGRATED import #{session.id}")

    print(f"Done: {migrated} migrated, {missing} missing local files.")
    if missing:
        print("The missing files remain unchanged in the database; recover them from backup if available.")


if __name__ == "__main__":
    main()
