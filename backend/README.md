# Backend (FastAPI)

FastAPI foundation for authentication and banking APIs.

## Layered modules (clean architecture foundation)

- `app/api`: HTTP transport only (routes/dependencies)
- `app/application`: use-case orchestration contracts
- `app/domain`: business contracts and abstractions
- `app/infrastructure`: database/security/external adapters
- `app/core`: config/logging/exceptions/startup wiring
- `tests`: foundational API and unit tests

No business logic is implemented yet.

## Current backend foundation includes

- App factory startup wiring with centralized router/handler setup
- API versioning under `/api/v1`
- Liveness/readiness health endpoints
- Readiness policy: `200` when DB is reachable, `503` degraded when DB is unavailable
- Synchronous SQLAlchemy + PostgreSQL connection foundation
- Alembic migration configuration and baseline migration scaffold
- Typed environment settings with `.env` loading
- JWT access/refresh token helpers (foundation only)
- Structured exception handling with consistent error envelopes
- Human-readable logs by default and optional JSON mode
- Face recognition integration boundary via interfaces/adapters

## Local commands

```bash
cd /tmp/workspace/santty1906/LandaProject/backend
pip install -r requirements/dev.txt
```

Run API:

```bash
uvicorn app.main:app --reload
```

Run checks:

```bash
ruff check app tests
python -m compileall app
pytest
```

Run migrations:

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe_change"
alembic downgrade -1
```
