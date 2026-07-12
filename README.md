# LANDA Bank

A lightweight, mobile-friendly banking prototype built with Flask, SQLite, and Bootstrap 5. Features facial recognition via DeepFace (with liveness/anti-spoofing detection and eye-openness verification) and installable PWA support.

> **Academic project note:** this codebase went through two full rounds of QA remediation, mapped to ISO/IEC 27001 Annex A controls. See `docs/Plan_Pruebas_LANDA.docx` for the full test plan, defect log, and control-by-control justification.

## Features

- **Mobile & Desktop Banking UI** — responsive interface that adapts from a phone-width card to a centered desktop layout
- **User Authentication** — register, login, logout with `scrypt` password hashing (via Werkzeug)
- **Session Management** — secure, signed Flask sessions with 30-minute expiration and audit logging
- **Account Lockout** — automatic lockout after 5 failed login attempts within 15 minutes
- **Face ID (Optional)** — enroll 3 face angles, log in with your camera using DeepFace
  - Liveness detection (anti-spoofing) rejects photos, screens, and videos
  - Rejects captures with closed eyes (Eye Aspect Ratio check via MediaPipe)
  - Rejects captures where the face is cropped by the image edge
  - Requires a **trusted device** (a browser that already logged in with a password) as a second authentication factor
  - Biometric data encrypted with a per-user derived key (not a single shared key)
- **Audit Trail** — every login attempt is logged with IP, timestamp, and outcome
- **Security Headers** — CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS (on HTTPS)
- **PWA Ready** — install on Android/iOS home screen, works offline for cached assets
- **SQLite Database** — zero-config, file-based persistence

## Architecture

```
Monolithic Flask app
├── Server-rendered HTML (Jinja2 + Bootstrap 5)
├── Vanilla JavaScript (no build step, no npm)
├── SQLite via SQLAlchemy ORM
└── DeepFace + RetinaFace + PyTorch + MediaPipe for facial recognition (optional)
```

Full architecture documentation: [docs/architecture.md](docs/architecture.md)

## Project Structure

```
backend/
├── app/                    # Application package
│   ├── app.py              # Flask app factory + security headers
│   ├── config.py           # Configuration (fails fast on invalid secrets)
│   ├── models.py           # SQLAlchemy models (User, AuditLog, TrustedDevice)
│   ├── auth.py             # Authentication routes + account lockout
│   ├── routes.py           # Dashboard, settings, face API, trusted-device gating
│   ├── security.py         # Password hashing, decorators, trusted-device logic
│   ├── face_service.py     # DeepFace/RetinaFace/MediaPipe integration
│   ├── templates/          # HTML templates
│   └── static/             # CSS, JS, PWA files
├── tests/                  # Pytest test suite (60+ tests)
├── instance/               # SQLite DB + encrypted face data (gitignored)
├── run.py                  # Entry point
├── requirements.txt
├── Dockerfile
└── pytest.ini
```

## Frontend (Flutter) — not part of this submission

This repository also contains a `frontend/` folder with a Flutter project. It was built in a single initial commit and never continued: it has a working-looking authentication flow (login, splash, home pages, clean architecture, planned biometric auth support), but no session management or dashboard screen, so it doesn't connect to the rest of the banking functionality. It has not been compiled or run since that first commit.

**This folder is not part of the evaluated deliverable.** The actual, functional application is the Flask web app described in this README. See [`frontend/README.md`](frontend/README.md) for details if you're curious about its state.

## Installation

### Prerequisites

- **Python 3.11** (required — newer versions like 3.13/3.14 don't yet have precompiled wheels for numpy/opencv/tensorflow and will fail to install with compilation errors)
- Git
- Webcam (optional, for Face ID features)
- **Windows users:** clone the repo to a short path outside of OneDrive (e.g. `C:\landa-banking-system`), not inside `C:\Users\...\OneDrive\...`. Some dependencies (TensorFlow) generate long internal file paths that exceed Windows' path length limit if the repo is nested too deep inside a synced folder.

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd landa-banking-system/backend

# Create the virtual environment (must be Python 3.11)
py -3.11 -m venv venv        # Windows
python3.11 -m venv venv      # macOS / Linux

# Activate it
venv\Scripts\Activate.ps1    # Windows PowerShell
source venv/bin/activate     # macOS / Linux
```

> If PowerShell blocks the activation script, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` once in that terminal, then try activating again.

```bash
# Install dependencies (takes several minutes — TensorFlow, DeepFace, PyTorch, and MediaPipe are large)
pip install -r requirements.txt
```

> **Known dependency gotchas**, in case you hit them: `opencv-python` must stay pinned to the exact version in `requirements.txt` (a newer release shipped without its face-detection data files); `mediapipe` and `tensorflow` can conflict on their `protobuf` version — if you hit an import error, run `pip install --upgrade "protobuf>=6.31.1,<7"`.

### Required environment variables (the app will not start without these)

```bash
cp .env.example .env
```

Then open `.env` and generate **two distinct** real values — the app validates both at startup and refuses to run with placeholder or missing values:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Run that command twice and paste one result into `SECRET_KEY` and the other into `ENCRYPTION_KEY`. Every developer/environment should generate their **own** keys — never share or reuse one from another machine.

```env
SECRET_KEY=<paste first generated key here>
ENCRYPTION_KEY=<paste second generated key here>
SESSION_COOKIE_SECURE=true
SESSION_TIMEOUT_MINUTES=30
FACE_DETECTOR_BACKEND=retinaface
FACE_MIN_CONFIDENCE=0.80
FACE_ANTI_SPOOFING=true
FACE_CHECK_EYES_OPEN=true
FACE_MIN_EYE_ASPECT_RATIO=0.20
```

### Run

```bash
python run.py
```

Open **http://localhost:5000** in your browser. On the first Face ID enrollment or login attempt, DeepFace/MediaPipe will download their models automatically (a few hundred MB combined) — this only happens once, and requires an internet connection at that moment.

## Testing

```bash
cd backend
pytest
```

Expect all tests passing with coverage above the 70% threshold enforced in `pytest.ini`.

With an HTML coverage report:

```bash
pytest --cov=app --cov-report=html
```

Test categories:

| Test file                | What it covers                                                                 |
| ------------------------ | -------------------------------------------------------------------------------|
| `tests/test_auth.py`     | Registration, login, logout, password policy, account lockout                  |
| `tests/test_routes.py`   | Protected routes, settings, face API endpoints, trusted-device gating          |
| `tests/test_security.py` | Password hashing, trusted-device token hashing                                 |
| `tests/test_face.py`     | Face embedding logic, framing/quality checks, eye-openness, per-user key derivation |

## DeepFace Setup

DeepFace, RetinaFace, and the anti-spoofing/eye-detection models download automatically on first use. Combined, expect a few hundred MB across all of them — ensure you have an internet connection for the first run of each feature (enrollment and login-verify).

```bash
# Test DeepFace is working
python -c "from deepface import DeepFace; print('DeepFace ready')"
```

### Face ID Usage

1. Register and log in with your password — this also marks your current browser as a **trusted device**
2. Go to **Settings** → click **Enroll Face**
3. Capture 3 angles: frontal, left, right (each must show your full, unobstructed, open-eyed face)
4. Click **Save** — embeddings are encrypted with a key derived specifically for your account and stored locally
5. On subsequent logins **from that same trusted device**, use the camera for biometric auth
6. Password login always available as a fallback, and is **required** the first time on any new device — Face ID will not even appear as an option until you've logged in with a password on that device at least once

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

- HTTPS or localhost (required for service workers and camera access)
- Modern browser (Chrome 67+, Safari 12.1+, Firefox 68+)
- To test from a phone, `localhost` and your PC's local network IP won't allow camera access (no HTTPS) — use a tool like [ngrok](https://ngrok.com) to get a temporary HTTPS URL: `ngrok http 5000`

## Security Considerations

| Area                  | Implementation                                                                 |
| ---------------------- | ------------------------------------------------------------------------------|
| Passwords              | `scrypt` hashing via Werkzeug, minimum 8 characters with letters and numbers   |
| Account lockout         | 5 failed attempts within 15 minutes locks the account temporarily             |
| Rate limiting           | Per-endpoint limits (e.g. 5/min on login, 3/min on face login-verify)         |
| Sessions                | Signed, `HttpOnly`, `SameSite=Lax` cookies; 30-minute expiration              |
| CSRF                    | Flask-WTF tokens on all state-changing forms; JSON APIs exempted and protected by session + rate limiting instead |
| HTTP security headers   | CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS (HTTPS only) |
| Second factor (Face ID) | Biometric login requires a previously trusted (password-authenticated) device |
| Face liveness           | Anti-spoofing (PyTorch) rejects photos/screens/video; Eye Aspect Ratio (MediaPipe) rejects closed-eye captures |
| Face data               | Embeddings encrypted with Fernet, using a key derived per-user (HKDF + individual salt), not a single shared key |
| Face images             | Temporary capture files deleted immediately after embedding extraction, even on error (`try/finally`) |
| Audit log               | All auth events logged with user, IP, timestamp, and outcome                 |
| SQLite                  | Database in `instance/` (gitignored)                                          |

**Known limitations (documented, not yet resolved):**
- Face recognition is noticeably slow on a CPU-only machine, since RetinaFace + anti-spoofing + eye detection all run per attempt.
- The on-screen face guide circle is a visual aid only — the actual captured frame is the full camera image, not a crop of the circle. The server does still reject genuinely cropped/edge-touching faces, but the guide doesn't visually enforce this before capture.

**Before deploying to production (beyond this academic scope):**
- Move secrets to a dedicated vault (e.g. HashiCorp Vault, AWS Secrets Manager) instead of a `.env` file
- Use a production database instead of SQLite
- Enforce real HTTPS with a trusted certificate
- Move the rate limiter's storage to Redis (in-memory storage isn't reliable across multiple worker processes)

## Software Quality Goals

| Goal            | Approach                                            |
| --------------- | --------------------------------------------------- |
| Testability     | Pytest with fixtures, SQLite in-memory test DB      |
| Maintainability | Flat module structure, clear separation of concerns |
| Simplicity      | No microservices, no build step                     |
| Accessibility   | Bootstrap 5 semantic HTML, responsive design (mobile and desktop) |
| Auditability    | Every auth action logged with timestamp, IP, and outcome; each security control traced to an ISO/IEC 27001 Annex A control |

## Future Improvements

- [x] ~~Two-factor authentication (TOTP)~~ — implemented as trusted-device authentication instead of TOTP; per-transaction 2FA for sensitive actions remains a future option
- [ ] Transaction history with pagination
- [ ] Admin dashboard for user management
- [ ] Email verification on registration
- [ ] Password reset flow
- [ ] HTTPS enforcement in all environments
- [ ] End-to-end testing with Playwright
- [ ] GPU-backed inference or lighter models to reduce Face ID latency
- [ ] Rigorous cancelable biometrics (current per-user key derivation only mitigates isolated leaks, not a full master-key compromise)

## License

University project — educational purposes only. Not intended for production banking use.
