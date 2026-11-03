# Run PharmaMind behind Cloudflare Tunnel

The login error `Failed to fetch` was caused by the frontend build pointing at `http://localhost:8000`. On a visitor's browser, `localhost` means that visitor's own computer, not the computer running PharmaMind. The API client now ignores a loopback API/WebSocket URL when opened on a public hostname, and the Vite dev server proxies API/WebSocket paths to the local FastAPI service.

## Recommended: tunnel the combined app

FastAPI serves both the built React app and API on port 8000. Keep the frontend and backend on one public origin so REST calls, WebSockets, and browser cookies/storage don't require cross-origin configuration.

1. Ensure the root `.env` has a working PostgreSQL `DATABASE_URL` and a `JWT_SECRET`.
2. Build the frontend:

   ```powershell
   Set-Location frontend
   npm ci
   npm run build
   Set-Location ..
   ```

3. Start the backend (it runs database migrations first if using the Dockerfile; for local Uvicorn, run Alembic once):

   ```powershell
   python -m alembic -c backend/alembic.ini upgrade head
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```

4. In another terminal, create a temporary public tunnel to FastAPI:

   ```powershell
   cloudflared tunnel --url http://localhost:8000
   ```

5. Open the `https://...trycloudflare.com` URL printed by `cloudflared`. Check `/health` and `/health/db` on that same URL, then try login.

## If tunneling the Vite dev server

Run FastAPI on port 8000 and Vite on port 5173. The Vite config proxies `/auth`, `/users`, `/families`, `/imports`, `/health`, and `/ws` to FastAPI, so tunnel only the Vite port:

```powershell
cloudflared tunnel --url http://localhost:5173
```

This is for temporary development only. Keep both processes running while others use the link. Do not tunnel port 5173 if you have built the app and want a stable single-service preview; use the combined app on port 8000 instead.

## Troubleshooting

- `https://<tunnel-host>/health` should return `{"status":"ok"}`.
- `https://<tunnel-host>/health/db` should return `{"status":"ok","database":"connected"}`.
- If those URLs fail, check that FastAPI is running on the machine where `cloudflared` runs and that the backend has a valid database URL.
- Restart Vite after changing `frontend/.env`; Vite reads environment files at startup. For the same-origin tunnel setup, leave `VITE_API_BASE_URL` and `VITE_WS_BASE_URL` empty.
- Quick Tunnel URLs change when the tunnel process restarts. A named tunnel/custom hostname is needed for a stable address.
