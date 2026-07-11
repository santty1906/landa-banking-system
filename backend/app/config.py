import os
from datetime import timedelta

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()


def _get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"La variable de entorno '{name}' es obligatoria y no está definida. "
            f"Copia .env.example a .env y complétala."
        )
    return value


class Config:
    SECRET_KEY = _get_required_env("SECRET_KEY")
    ENCRYPTION_KEY = _get_required_env("ENCRYPTION_KEY")

    # Falla rápido en el arranque si la clave no es una clave Fernet válida,
    # en vez de fallar silenciosamente en medio de una verificación facial real.
    try:
        Fernet(ENCRYPTION_KEY.encode())
    except Exception as exc:
        raise RuntimeError(
            "ENCRYPTION_KEY no es una clave Fernet válida. Genera una nueva con:\n"
            "python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\""
        ) from exc

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    FACE_MATCH_THRESHOLD = float(os.environ.get("FACE_MATCH_THRESHOLD", "0.35"))
    FACE_MODEL_NAME = os.environ.get("FACE_MODEL_NAME", "Facenet512")
    FACE_DETECTOR_BACKEND = os.environ.get("FACE_DETECTOR_BACKEND", "opencv")
    FACE_ENFORCE_DETECTION = os.environ.get("FACE_ENFORCE_DETECTION", "true").lower() == "true"
    FACE_TARGET_SIZE = int(os.environ.get("FACE_TARGET_SIZE", "224"))
    FACE_MIN_ANGLE_DISTANCE = float(os.environ.get("FACE_MIN_ANGLE_DISTANCE", "0.15"))

    # --- Sesiones / cookies (ISO 27001 A.8.5 - Autenticación segura) ---
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.environ.get("SESSION_TIMEOUT_MINUTES", "30"))
    )
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "http")
