import hashlib
import re
import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import current_app, flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .models import TrustedDevice, User, db

PASSWORD_MIN_LENGTH = 8

TRUSTED_DEVICE_COOKIE = "landa_trusted_device"
TRUSTED_DEVICE_DAYS = 90


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def is_strong_password(password: str) -> bool:
    """Política mínima de contraseñas (ISO 27001 A.8.5)."""
    if len(password) < PASSWORD_MIN_LENGTH:
        return False
    has_letter = re.search(r"[A-Za-z]", password) is not None
    has_digit = re.search(r"\d", password) is not None
    return has_letter and has_digit


def _hash_device_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_trusted_device(response, user_id):
    """
    Marca el dispositivo actual como confiable para este usuario, después de
    un login exitoso con contraseña. Face ID solo funcionará después en
    dispositivos que hayan pasado por aquí (segundo factor: "algo que tienes").
    """
    token = secrets.token_urlsafe(32)
    token_hash = _hash_device_token(token)

    db.session.add(TrustedDevice(user_id=user_id, token_hash=token_hash))
    db.session.commit()

    response.set_cookie(
        TRUSTED_DEVICE_COOKIE,
        token,
        max_age=60 * 60 * 24 * TRUSTED_DEVICE_DAYS,
        httponly=True,
        secure=current_app.config.get("SESSION_COOKIE_SECURE", True),
        samesite="Lax",
    )
    return response


def is_trusted_device(user_id) -> bool:
    """Verifica si el navegador actual ya inició sesión con contraseña antes."""
    token = request.cookies.get(TRUSTED_DEVICE_COOKIE)

    if not token:
        return False

    token_hash = _hash_device_token(token)
    device = TrustedDevice.query.filter_by(user_id=user_id, token_hash=token_hash).first()

    if not device:
        return False

    device.last_used_at = datetime.now(timezone.utc)
    db.session.commit()
    return True


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")

        if not user_id:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        user = db.session.get(User, user_id)

        if not user:
            session.clear()
            flash("Invalid session.", "warning")
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return wrapper
