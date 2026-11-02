# Free-hosted preview

This setup publishes the existing React UI and FastAPI API on one Render web service and one free `onrender.com` subdomain. It is for a demo with synthetic data only. It is not a production host for real health or prescription records.

## What is included

- `Dockerfile` builds the React client and runs FastAPI in the same image.
- FastAPI serves the SPA and API from the same origin, so browser API and WebSocket URLs resolve to the hosted domain by default.
- `render.yaml` creates a Singapore region Free web service, uses a generated JWT secret, and asks for `DATABASE_URL` as a secret.
- The container runs Alembic migrations before starting Uvicorn.

Render assigns a hostname ending in `.onrender.com`. The exact hostname is confirmed by Render when the service is created; service names are not a permanent domain reservation.

## Deploy steps

1. Open the **Deploy to Render** button in the repository README and sign in/connect the GitHub repository if prompted. Do not include `.env`, `storage/imports/`, backups, or real health data.
2. Create a Supabase Free Postgres project for demo data. Copy its Session Pooler connection URL. Adapt the scheme for this application to `postgresql+psycopg://` and ensure `sslmode=require` is present. URL-encode special characters in the database password.
3. In Render, review the Blueprint resources. Enter the database URL when asked for the unsynchronized `DATABASE_URL` value. The Blueprint has automatic deploys disabled, so future Git pushes do not unexpectedly redeploy this preview.
4. Wait for the Docker build and first Alembic migration. Open the Render service URL and confirm `/health` returns `{"status":"ok"}`.
5. For a Flutter build, set `API_BASE_URL` to the exact Render URL using `--dart-define`; production builds must use HTTPS.

## Free tier limits

The Render Free web service sleeps after 15 minutes without inbound traffic and takes about a minute to wake. Its filesystem is ephemeral. Supabase Free provides a 500 MB database and pauses projects after a week of low activity; it does not include automatic backups. Prescription uploads currently use local filesystem storage, so uploaded source files can disappear after a restart/redeploy. Do not enter real family health data, prescriptions, or credentials into this preview.

Before a real pilot, move to persistent storage with backups, use a paid/managed database and hosting plan, add a private object store for uploads, configure monitoring and restore tests, and finish the missing OCR/AI/notification services. See the [full deployment plan](../../task/PRODUCTION_SERVER_DEPLOYMENT_PLAN.md).

Official limits: [Render Free services](https://render.com/docs/free), [Supabase Free Postgres](https://supabase.com/kb/faqs/platform/free-postgres-for-side-projects).
