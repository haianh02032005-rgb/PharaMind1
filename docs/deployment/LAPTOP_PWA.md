# PharmaMind AI on laptops (PWA)

The React frontend is an installable Progressive Web App for Windows, macOS,
Linux and ChromeOS. A public HTTPS deployment is required for browser
installation; `localhost` and `127.0.0.1` are also accepted for development.

## Build and verify

```powershell
cd frontend
npm ci
npm test
npm run build
npm run preview -- --host 127.0.0.1
```

Open `http://127.0.0.1:4173`. In Chrome or Edge, use **Cài trên laptop** when
the browser exposes the installation prompt. The installed app appears in the
Start menu, taskbar or application launcher and opens in a standalone window.

## Production deployment

The repository Dockerfile builds the PWA and serves it together with FastAPI
from one origin. Deploy the repository as a Docker web service and set
`DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS=[]` and `DEBUG=false`. The service
must be reachable over HTTPS.

The service worker caches only the application shell, generated JavaScript/CSS
assets and 3D model files. Authentication, family, prescription, import,
health-check and WebSocket routes are deliberately excluded. Health and
prescription data are therefore never placed in the browser Cache API.

Free preview hosting is suitable only for synthetic demo data. Use persistent
PostgreSQL and S3-compatible object storage with backups before entering real
health information.
