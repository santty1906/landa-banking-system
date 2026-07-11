import os

from flask import Flask, request
from flask_wtf.csrf import CSRFProtect

from .config import Config
from .models import db
from .extensions import limiter

csrf = CSRFProtect()


def _register_security_headers(app):
    """Cabeceras de seguridad HTTP (ISO 27001 A.8.26 - Seguridad de aplicaciones)."""

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault(
            "Permissions-Policy", "camera=(self), geolocation=(), microphone=()"
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net;",
        )
        if request.is_secure:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


def create_app(config_class=Config, database_uri=None, upload_folder=None):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar seguridad
    csrf.init_app(app)
    limiter.init_app(app)
    _register_security_headers(app)

    os.makedirs(app.instance_path, exist_ok=True)

    db_uri = database_uri or os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(app.instance_path, 'landa.db')}"
    )

    up_folder = upload_folder or os.environ.get(
        "UPLOAD_FOLDER",
        os.path.join(app.instance_path, "faces")
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["UPLOAD_FOLDER"] = up_folder

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    from .auth import auth_bp
    from .routes import routes_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(routes_bp)

    with app.app_context():
        db.create_all()

    return app
