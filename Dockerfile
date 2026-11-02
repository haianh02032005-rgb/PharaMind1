# Build the web client and serve it with FastAPI so preview and API share one
# free HTTPS origin/domain.
FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements-prod.txt ./requirements-prod.txt
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY backend/ ./backend/
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["sh", "-c", "alembic -c backend/alembic.ini upgrade head && python -m backend.app.db.seed_demo && uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
