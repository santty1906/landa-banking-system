HEAD

# LANDA Bank

A lightweight, mobile-friendly banking prototype built with Flask, SQLite, and Bootstrap 5. Features optional facial recognition via DeepFace pretrained models and installable PWA support.

## Features

- **Mobile Banking UI** — responsive, touch-friendly interface with bottom navigation
- **User Authentication** — register, login, logout with bcrypt password hashing
- **Session Management** — secure Flask sessions with audit logging
- **Face ID (Optional)** — enroll 3 face angles, log in with your camera using DeepFace
- **Audit Trail** — every login attempt is logged for security review
- **PWA Ready** — install on Android/iOS home screen, works offline for cached assets
- **SQLite Database** — zero-config, file-based persistence

## Architecture

```
Monolithic Flask app
├── Server-rendered HTML (Jinja2 + Bootstrap 5)
├── Vanilla JavaScript (no build step, no npm)
├── SQLite via SQLAlchemy ORM
└── DeepFace for facial recognition (optional)
```

Full architecture documentation: [docs/architecture.md](docs/architecture.md)

## Project Structure

```
backend/
├── app/                    # Application package
│   ├── app.py              # Flask app factory
│   ├── config.py           # Configuration
│   ├── models.py           # SQLAlchemy models
│   ├── auth.py             # Authentication routes
│   ├── routes.py           # Dashboard, settings, face API
│   ├── security.py         # Password hashing + decorators
│   ├── face_service.py     # DeepFace integration
│   ├── templates/          # HTML templates
│   └── static/             # CSS, JS, PWA files
├── tests/                  # Pytest test suite
├── instance/               # SQLite DB + face data (gitignored)
├── run.py                  # Entry point
├── requirements.txt
└── pytest.ini
```

## Installation

### Prerequisites

- Python 3.10+
- Webcam (optional, for Face ID features)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd LandaProject

# Create virtual environment
cd backend
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional — defaults work for development)
cp .env.example .env
```

### Run

```bash
python run.py
```

Open **http://localhost:5000** in your browser.

## Testing

```bash
cd backend
pytest
```

With coverage report:

```bash
pytest --cov=app --cov-report=html
```

Test categories:

| Test file                | What it covers                                      |
| ------------------------ | --------------------------------------------------- |
| `tests/test_auth.py`     | Registration, login, logout, validation, edge cases |
| `tests/test_routes.py`   | Protected routes, settings, face API endpoints      |
| `tests/test_security.py` | Password hashing unit tests                         |
| `tests/test_face.py`     | Face service edge cases                             |

## DeepFace Setup

DeepFace downloads pretrained models on first use (~500MB). Ensure you have an internet connection for the initial run.

```bash
# Test DeepFace is working
python -c "from deepface import DeepFace; print('DeepFace ready')"
```

The first call to `DeepFace.represent()` will download the Facenet512 model automatically.

### Face ID Usage

1. Register and log in
2. Go to **Settings** → click **Enroll Face**
3. Capture 3 angles: frontal, left, right
4. Click **Save** — embeddings are stored locally
5. On subsequent logins, use the camera for biometric auth
6. Password login always available as fallback

## PWA Installation

### Android (Chrome)

1. Open http://localhost:5000 in Chrome
2. Tap the "Install" badge in the address bar (or menu → "Add to Home Screen")
3. LANDA Bank will appear as an installed app

### iOS (Safari)

1. Open http://localhost:5000 in Safari
2. Tap the Share button → "Add to Home Screen"
3. Name the app → "Add"

### Requirements

- HTTPS or localhost (required for service workers)
- Modern browser (Chrome 67+, Safari 12.1+, Firefox 68+)

## Security Considerations

| Area        | Implementation                                 |
| ----------- | ---------------------------------------------- |
| Passwords   | bcrypt hashing via Werkzeug                    |
| Sessions    | Signed cookies (Flask SECRET_KEY)              |
| Face data   | Stored locally as pickled numpy arrays         |
| Face images | Deleted immediately after embedding extraction |
| Audit log   | All auth events logged with IP and timestamp   |
| SQLite      | Database in `instance/` (gitignored)           |

**Before deploying:**

- Change `SECRET_KEY` in `.env` to a strong random value
- Set `DATABASE_URL` to a persistent path
- Consider rate limiting on login endpoints
- Review `FACE_MATCH_THRESHOLD` for your security needs

## Software Quality Goals

| Goal            | Approach                                            |
| --------------- | --------------------------------------------------- |
| Testability     | Pytest with fixtures, SQLite in-memory test DB      |
| Maintainability | Flat module structure, clear separation of concerns |
| Simplicity      | No microservices, no Docker, no build step          |
| Accessibility   | Bootstrap 5 semantic HTML, responsive design        |
| Auditability    | Every auth action logged with timestamp and IP      |

## Future Improvements

- [ ] Two-factor authentication (TOTP)
- [ ] Transaction history with pagination
- [ ] Admin dashboard for user management
- [ ] Email verification on registration
- [ ] Password reset flow
- [ ] Rate limiting middleware
- [ ] HTTPS enforcement
- [ ] End-to-end testing with Playwright

## License

# University project — educational purposes only. Not intended for production banking use.

# Landa-Banking-System
