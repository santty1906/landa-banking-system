import re
from functools import wraps
from flask import flash, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .models import User, db

PASSWORD_MIN_LENGTH = 8


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
