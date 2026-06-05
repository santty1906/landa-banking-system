# Testing Guide

## Test suites

- Unit: isolated module behavior (`unit`)
- API: endpoint contracts and behavior (`api`)
- Security/Auth: authentication and unauthorized access checks (`security`, `auth`)
- Integration: real PostgreSQL integration checks (`integration`)
- Face contract: provider-independent facial recognition tests (`face_contract`)
- Face provider: heavy provider tests for manual/nightly pipelines (`face_provider`)

## Backend commands

From repository root:

```bash
cd backend
ruff check app tests
python -m compileall app
pytest
```

Run integration tests explicitly (requires a running PostgreSQL instance):

If you're using the repository's Docker Compose DB (`docker compose up -d db`), it exposes Postgres on host port 5433 by default:

    POSTGRES_HOST=localhost POSTGRES_PORT=5433 pytest -m integration -o addopts=''

Run heavy provider tests explicitly:

```bash
cd backend
RUN_FACE_PROVIDER_TESTS=1 pytest -m face_provider -o addopts=''
```
