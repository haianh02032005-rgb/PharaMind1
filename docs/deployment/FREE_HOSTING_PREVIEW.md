# Free-hosted preview

This setup publishes the existing React UI and FastAPI API from one Dockerfile-backed public web service. It is for a demo with synthetic data only. It is not a production host for real health or prescription records.

## Recommended: Koyeb + Neon

Use the Koyeb button in the repository README to deploy the public GitHub repository with its root `Dockerfile`. The app uses one Koyeb web service for the frontend and API, and Neon Free for PostgreSQL. This avoids Render's 30-day expiry for its free PostgreSQL databases.

At Koyeb's deploy screen, select the Free instance in Frankfurt or Washington, expose port `8000` as HTTP on `/`, and add `/health` as the health check. Add these runtime variables:

- `APP_NAME=PharmaMind AI`
- `APP_VERSION=0.1.0`
- `DEBUG=false`
- `DEFAULT_TIMEZONE=Asia/Ho_Chi_Minh`
- `CORS_ORIGINS=[]`
- `PORT=8000`
- `DATABASE_URL`: Neon direct PostgreSQL connection string, stored as a secret
- `JWT_SECRET`: unique random value of at least 32 characters, stored as a secret

Create the Neon database first so the `DATABASE_URL` secret is ready before the first deploy. On success, Koyeb shows a public HTTPS URL ending in `.koyeb.app`. Detailed steps and current free-tier limits are in [deploy/koyeb/README.md](../../deploy/koyeb/README.md).

Koyeb's free instance has 512 MB RAM and 0.1 vCPU, and scales to zero after one hour without traffic. Neon Free includes 1 GB of PostgreSQL storage and 100 compute-hours per month, and suspends compute after five minutes of inactivity. These tiers are for a low-traffic demo, not a production availability guarantee. Uploads use local storage unless S3-compatible storage is configured; the container filesystem is ephemeral. Do not enter real family health data, prescriptions, or credentials into this preview. See [persistent upload storage and backups](UPLOAD_STORAGE_AND_BACKUPS.md) before configuring an object bucket.

Official limits: [Koyeb Free instance](https://www.koyeb.com/docs/reference/instances), [Neon Free plan](https://github.com/neondatabase/website/blob/main/content/faqs/free-plan-limits-and-quotas.md).

## Alternative: Render

The repository also has a Render Blueprint that creates a Singapore Free web service and Free Postgres database. Render's free database expires after 30 days, so use it only for a short-lived preview. The service sleeps after 15 minutes without traffic.

### What is included

- `Dockerfile` builds the React client and runs FastAPI in the same image.
- FastAPI serves the SPA and API from the same origin, so browser API and WebSocket URLs resolve to the hosted domain by default.
- `render.yaml` creates a Singapore region Free web service and Free Postgres database, uses a generated JWT secret, and wires `DATABASE_URL` automatically.
- The container runs Alembic migrations before starting Uvicorn.

Render assigns a hostname ending in `.onrender.com`. The exact hostname is confirmed by Render when the service is created; service names are not a permanent domain reservation.

### Deploy steps

1. Open the **Deploy to Render** button in the repository README and sign in/connect the GitHub repository if prompted. Do not include `.env`, `storage/imports/`, backups, or real health data.
2. Review the Blueprint: it creates a Singapore Free web service, a Free PostgreSQL database, and generates the JWT secret. No `DATABASE_URL` needs to be entered.
3. Wait for the Docker build and first Alembic migration. Open the Render service URL and confirm `/health` returns `{"status":"ok"}`.
4. For a Flutter build, set `API_BASE_URL` to the exact Render URL using `--dart-define`; production builds must use HTTPS.

If the Blueprint was already created from the previous version that expected a manually entered `DATABASE_URL`, open the Blueprint in the Render Dashboard and run **Manual Sync** to add the database resource and update the service environment before retrying the deploy.

### Free tier limits

The Render Free web service sleeps after 15 minutes without inbound traffic and takes about a minute to wake. Its filesystem is ephemeral. A Render Free Postgres database expires after 30 days, has no backups, and is limited to 1 GB. Uploads use local storage unless S3-compatible storage is configured; the container filesystem is ephemeral. Do not enter real family health data, prescriptions, or credentials into this preview.

Before a real pilot, use a paid/managed database and hosting plan, configure a private object store and separate backups for uploads, configure monitoring and restore tests, benchmark OCR on de-identified real prescriptions, and finish the missing AI/notification services. See the [OCR deployment guide](OCR_PRODUCTION.md), [upload storage guide](UPLOAD_STORAGE_AND_BACKUPS.md), and [full deployment plan](../../task/PRODUCTION_SERVER_DEPLOYMENT_PLAN.md).

Official limits: [Render Free services and Postgres](https://render.com/docs/free).
