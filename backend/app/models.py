from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    face_enrolled = db.Column(db.Boolean, default=False)
    # Salt individual para derivar la clave de cifrado biométrico de este
    # usuario (ver _derive_user_key en face_service.py). Permite "revocar"
    # la plantilla de una sola persona sin afectar a las demás.
    bio_salt = db.Column(db.String(64), nullable=True)

    audits = db.relationship("AuditLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    trusted_devices = db.relationship("TrustedDevice", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(200), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    success = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<AuditLog {self.action} at {self.timestamp}>"


class TrustedDevice(db.Model):
    """
    Dispositivo que ya inició sesión con contraseña al menos una vez.
    El login por Face ID solo se permite si viene de uno de estos
    dispositivos ya reconocidos (segundo factor: "algo que tienes").
    """
    __tablename__ = "trusted_devices"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<TrustedDevice user_id={self.user_id}>"
