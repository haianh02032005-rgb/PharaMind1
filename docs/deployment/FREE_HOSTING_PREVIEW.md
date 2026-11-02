# Free-hosted preview

This setup publishes the existing React UI and FastAPI API on one Render web service and one free `onrender.com` subdomain. It is for a demo with synthetic data only. It is not a production host for real health or prescription records.

## What is included

- `Dockerfile` builds the React client and runs FastAPI in the same image.
- FastAPI serves the SPA and API from the same origin, so browser API and WebSocket URLs resolve to the hosted domain by default.
- `render.yaml` creates a Singapore region Free web service and Free Postgres database, uses a generated JWT secret, and wires `DATABASE_URL` automatically.
- The container runs Alembic migrations before starting Uvicorn.

Render assigns a hostname ending in `.onrender.com`. The exact hostname is confirmed by Render when the service is created; service names are not a permanent domain reservation.

## Deploy steps

1. Open the **Deploy to Render** button in the repository README and sign in/connect the GitHub repository if prompted. Do not include `.env`, `storage/imports/`, backups, or real health data.
2. Review the Blueprint: it creates a Singapore Free web service, a Free PostgreSQL database, and generates the JWT secret. No `DATABASE_URL` needs to be entered.
3. Wait for the Docker build and first Alembic migration. Open the Render service URL and confirm `/health` returns `{"status":"ok"}`.
4. For a Flutter build, set `API_BASE_URL` to the exact Render URL using `--dart-define`; production builds must use HTTPS.

If the Blueprint was already created from the previous version that expected a manually entered `DATABASE_URL`, open the Blueprint in the Render Dashboard and run **Manual Sync** to add the database resource and update the service environment before retrying the deploy.

## Free tier limits

The Render Free web service sleeps after 15 minutes without inbound traffic and takes about a minute to wake. Its filesystem is ephemeral. A Render Free Postgres database expires after 30 days, has no backups, and is limited to 1 GB. Prescription uploads currently use local filesystem storage, so uploaded source files can disappear after a restart/redeploy. Do not enter real family health data, prescriptions, or credentials into this preview.

Before a real pilot, move to persistent storage with backups, use a paid/managed database and hosting plan, add a private object store for uploads, configure monitoring and restore tests, and finish the missing OCR/AI/notification services. See the [full deployment plan](../../task/PRODUCTION_SERVER_DEPLOYMENT_PLAN.md).

Official limits: [Render Free services and Postgres](https://render.com/docs/free).
