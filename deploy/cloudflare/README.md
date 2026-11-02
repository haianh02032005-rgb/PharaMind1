# Deploy PharmaMind on Cloudflare

This configuration runs the existing Docker application (Vite frontend and FastAPI backend) in a Cloudflare Container behind a Worker. It keeps the application's existing PostgreSQL database and serves the UI and API from one HTTPS origin.

## Requirements

- A Cloudflare account with Workers Paid enabled. Containers are not available on the Free plan; the Workers Paid plan currently starts at $5/month, with container usage billed against its included allowance and then usage-based rates.
- Docker Desktop (or another Docker-compatible engine) running on the machine used for CLI deployment.
- A reachable PostgreSQL database. Use its PostgreSQL connection string as `DATABASE_URL`; Cloudflare does not create the database in this setup.
- Node.js and npm.

## Deploy

From `deploy/cloudflare`:

```powershell
npm install
npx wrangler login
npx wrangler secret put DATABASE_URL
npx wrangler secret put JWT_SECRET
npx wrangler deploy
```

Paste the database connection string only at the `DATABASE_URL` prompt. Generate a unique random value of at least 32 characters for `JWT_SECRET`. Do not commit secrets or put them in `wrangler.jsonc`.

Wrangler prints a `https://pharmamind-ai.<your-workers-subdomain>.workers.dev` URL after a successful deployment. The first request can take several minutes while Cloudflare provisions the container. Check `/health` and `/health/db` after it starts.

## Notes

- The existing container runs Alembic migrations when it starts. Configure a PostgreSQL database before the first request.
- Uploaded prescription files currently use the container filesystem, which is ephemeral. For durable uploads, move them to Cloudflare R2 before relying on uploads in production.
- Cloudflare's current Containers documentation lists the service as Workers Paid and requires Docker for a CLI deployment from a Dockerfile. See [Containers overview](https://developers.cloudflare.com/containers/) and [pricing](https://developers.cloudflare.com/containers/platform/pricing/).
