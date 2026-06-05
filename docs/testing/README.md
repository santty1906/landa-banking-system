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

Run integration tests explicitly:

```bash
cd backend
pytest -m integration -o addopts=''
```

Run heavy provider tests explicitly:

```bash
cd backend
RUN_FACE_PROVIDER_TESTS=1 pytest -m face_provider -o addopts=''
```
