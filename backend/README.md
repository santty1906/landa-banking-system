# Backend (FastAPI)

FastAPI foundation for authentication and banking APIs.

## Layered modules (clean architecture foundation)

- `app/api`: HTTP transport only (routes/dependencies)
- `app/application`: use-case orchestration contracts
- `app/domain`: business contracts and abstractions
- `app/infrastructure`: database/security/external adapters
- `app/core`: config/logging/exceptions/startup wiring
- `tests`: foundational API and unit tests

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
- FaceID MVP endpoints:
  - `POST /api/v1/auth/face/enroll`
  - `POST /api/v1/auth/face/login`

## FaceID workflow (MVP)

1. Client uploads image + `user_id` via multipart form-data.
2. Service validates image quality (size, resolution, brightness, blur, single-face detection).
3. DeepFace adapter generates facial embeddings.
4. Embeddings are encrypted before persistence.
5. Enrollment upserts one active embedding per user.
6. Login compares live embedding against decrypted stored embedding.
7. Every attempt is written to auth audit logs (success and failure).

### Security caveats

- Raw facial images are **not** stored permanently.
- Images are processed in-memory and temporary files are deleted immediately after adapter execution.
- Embeddings are stored encrypted at rest using `FACE_EMBEDDING_ENCRYPTION_KEY`.
- This is a university MVP and does not yet include liveness/anti-spoofing protections.

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

## FaceID environment variables

```env
FACE_RECOGNITION_MODEL=Facenet512
FACE_RECOGNITION_DETECTOR_BACKEND=opencv
FACE_MATCH_THRESHOLD=0.35
FACE_IMAGE_MAX_SIZE_BYTES=5000000
FACE_IMAGE_MIN_WIDTH=120
FACE_IMAGE_MIN_HEIGHT=120
FACE_IMAGE_MIN_BRIGHTNESS=35
FACE_IMAGE_MIN_LAPLACIAN_VARIANCE=80
FACE_EMBEDDING_ENCRYPTION_KEY=change_this_face_embedding_key
FACE_EMBEDDING_KEY_VERSION=v1
```
