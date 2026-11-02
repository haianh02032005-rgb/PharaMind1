# PharmaMind AI - Backend

FastAPI backend. Run from the repository root:

```bash
uvicorn backend.app.main:app --reload
```

Layering for every module in `app/modules/<name>/`:

```text
router.py -> service.py -> repository.py -> database
```

Database layer:

```text
app/db/base.py        Declarative Base (every model inherits it)
app/db/session.py     engine + SessionLocal
app/api/dependencies  get_db() - one session per request, always closed
app/models/           SQLAlchemy models (register new ones in __init__.py)
alembic/              migrations (URL is read from DATABASE_URL in .env)
```

Migrations (from `backend/`): `alembic upgrade head`.
Never use `Base.metadata.create_all()` to manage the schema.
