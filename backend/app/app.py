import os

from flask import Flask

from .config import Config
from .models import db


def create_app(config_class=Config, database_uri=None, upload_folder=None):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)

    db_uri = database_uri or os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'landa.db')}"
    )
    up_folder = upload_folder or os.environ.get(
        "UPLOAD_FOLDER", os.path.join(app.instance_path, "faces")
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
