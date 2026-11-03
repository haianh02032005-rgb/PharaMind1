# Persistent prescription uploads and backups

Prescription source files are private. The API now supports either a persistent
local directory or a private S3-compatible object bucket. For hosted deployments,
use object storage so uploads survive container replacement and server restart.

## Configure S3-compatible storage

Set these as deployment secrets/environment variables on the API service:

```dotenv
FILE_STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
S3_REGION=auto
S3_BUCKET=<private-bucket-name>
S3_ACCESS_KEY_ID=<api-token-access-key-id>
S3_SECRET_ACCESS_KEY=<api-token-secret>
S3_PREFIX=prescription-imports
```

For AWS S3, use the bucket's region and leave `S3_ENDPOINT_URL` empty. The app
does not set a public ACL; keep the bucket private and grant the app identity only
the object permissions needed to write uploads. R2's S3 API uses the account
endpoint and `auto` region. See Cloudflare's [S3 compatibility](https://developers.cloudflare.com/r2/api/s3/api/)
and [boto3 setup](https://developers.cloudflare.com/r2/examples/aws/boto3/).

New uploads are stored under `prescription-imports/family_<id>/member_<id>/`.
The database stores an `s3://bucket/key` locator in `import_sessions.storage_path`;
object contents are not exposed through a public URL.

## Move existing local uploads

Before deploying the new configuration, take a database backup and copy the
existing `storage/imports/` directory somewhere safe. Then configure the S3
variables and run this once from the repository root where the API can reach the
same database and the old files are present:

```powershell
$env:FILE_STORAGE_BACKEND = "s3"
python -m backend.scripts.migrate_import_files_to_s3
```

The command uploads each existing file, updates its database locator only after
the object upload succeeds, skips records whose local file is missing, and can be
run again safely. Keep the source directory and database backup until you verify
the object count and restore procedure.

## Backups and restore

Object storage provides persistence, but it is not by itself a backup. Schedule
the included mirror job daily or more often, with a separate private destination
bucket (preferably in another account or provider). The backup identity needs
read access to the source and write access to the destination. The job copies new
or changed objects and never deletes destination objects when source objects are
removed. Set bucket retention/versioning according to your recovery needs, and
alert on failed runs. Back up PostgreSQL on a compatible schedule because its
rows contain the object keys.

Configure these additional secrets for the backup job. `BACKUP_S3_ENDPOINT_URL`
may be empty for AWS S3; use the destination's endpoint for another S3-compatible
provider. Set `BACKUP_S3_REGION` to the destination region (use `auto` for R2).

```dotenv
BACKUP_S3_ENDPOINT_URL=https://<backup-account-id>.r2.cloudflarestorage.com
BACKUP_S3_REGION=auto
BACKUP_S3_BUCKET=<different-private-backup-bucket>
BACKUP_S3_ACCESS_KEY_ID=<backup-token-access-key-id>
BACKUP_S3_SECRET_ACCESS_KEY=<backup-token-secret>
```

Run this on a scheduler/worker that can reach the source and destination:

```powershell
python -m backend.scripts.backup_import_files
```

The app's bucket credentials and the backup job's credentials should be separate.
Periodically restore a sample object and a database backup into staging, then
confirm the restored rows point to files that can be read. Do not make either
bucket public to test access.

## Local and container deployments

For a single self-hosted server without object storage, set
`FILE_STORAGE_BACKEND=local` and point `FILE_STORAGE_LOCAL_PATH` at a mounted
persistent disk. Back up this directory and PostgreSQL together. The default
`storage/imports` path resolves from the repository root, not the process working
directory. A container's writable layer is not persistent storage: mount a named
volume or host directory at the configured path.

Never commit `.env`, bucket credentials, uploaded prescriptions, or backup files.
