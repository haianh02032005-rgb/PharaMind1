from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db
from backend.app.api.router import api_router
from backend.app.core.config import PROJECT_ROOT, settings


app = FastAPI(
    title=f"{settings.app_name} API",
    description="Backend API for PharmaMind AI",
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

frontend_dist = PROJECT_ROOT / "frontend" / "dist"
frontend_index = frontend_dist / "index.html"
if frontend_dist.is_dir():
    if (frontend_dist / "assets").is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=frontend_dist / "assets"),
            name="frontend-assets",
        )
    if (frontend_dist / "models").is_dir():
        app.mount(
            "/models",
            StaticFiles(directory=frontend_dist / "models"),
            name="frontend-models",
        )


@app.get("/")
def root(request: Request):
    accepts_html = "text/html" in request.headers.get("accept", "")
    if frontend_index.is_file() and accepts_html:
        return FileResponse(frontend_index)
    return {
        "name": settings.app_name,
        "status": "running",
        "version": settings.app_version,
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
    }


@app.get("/health/db")
def database_health(
    db: Session = Depends(get_db),
):
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }


@app.get("/{frontend_path:path}", include_in_schema=False)
def frontend_fallback(frontend_path: str):
    """Serve client-side routes when the optional production bundle exists."""
    if not frontend_index.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    if frontend_path.startswith(("auth/", "families/", "users/", "imports/", "ws/", "health/")):
        raise HTTPException(status_code=404, detail="Not found")
    static_file = frontend_dist / frontend_path
    if static_file.is_file():
        return FileResponse(static_file)
    return FileResponse(frontend_index)
