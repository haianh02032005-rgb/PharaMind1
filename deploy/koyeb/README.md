# Free community demo on Koyeb + Neon

This runs the current Docker app as one public Koyeb Web Service and keeps its relational data in Neon Postgres. It uses the existing root `Dockerfile`, so the React frontend and FastAPI API share the same public HTTPS origin.

## Free-tier behavior

- Koyeb's free Web Service has 512 MB RAM and 0.1 vCPU, is limited to one instance per organization, and scales to zero after one hour without traffic. It has no persistent volume, so local uploads are temporary. This is suitable for a low-traffic demo, not a production availability promise.
- Neon Free currently includes 1 GB of PostgreSQL storage and 100 compute-hours per project each month. The database scales to zero after five minutes of inactivity; the first request after idle can be slower.
- Both providers enforce quotas. Monitor usage if the link is shared widely.

## One-time setup

1. Create a free Neon project and database. Copy its PostgreSQL connection string from the Neon dashboard. Use the direct (non-pooler) connection string for this single long-running SQLAlchemy service.
2. In Koyeb, create a Web Service from the public GitHub repository `haianh02032005-rgb/PharaMind1`. Select the `main` branch, Dockerfile builder, repository root as the work directory, and `Dockerfile` as the Dockerfile path. Choose the Free instance and a free region (Frankfurt or Washington, D.C.).
3. Expose port `8000` as HTTP with route `/:8000`. Set the HTTP health check to `/health`.
4. Add these runtime variables in Koyeb. Store the two secret values as Koyeb Secrets and reference them; do not commit them:

   - `APP_NAME`: `PharmaMind AI`
   - `APP_VERSION`: `0.1.0`
   - `DEBUG`: `false`
   - `DEFAULT_TIMEZONE`: `Asia/Ho_Chi_Minh`
   - `CORS_ORIGINS`: `[]`
   - `PORT`: `8000`
   - `DATABASE_URL`: Neon PostgreSQL connection string (secret)
   - `JWT_SECRET`: unique random value of at least 32 characters (secret)

5. Deploy. Koyeb builds the Dockerfile, runs the Alembic migrations at startup, and shows the public `https://...koyeb.app` URL on the Service page. Verify `/health` and `/health/db`.

The code is already set to listen on `PORT`, serve the frontend and API together, and normalize Neon `postgresql://` connection strings for psycopg.
