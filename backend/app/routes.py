import re

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from .app import csrf
from .extensions import limiter
from .models import AuditLog, User, db
from .security import login_required

routes_bp = Blueprint("routes", __name__, template_folder="templates")


# ✅ VALIDACIÓN CORRECTA DE EMAIL (FIX DEFINITIVO)
def valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


@routes_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("routes.dashboard"))
    return redirect(url_for("auth.login"))


@routes_bp.route("/offline")
def offline():
    return render_template("offline.html")


@routes_bp.route("/manifest.json")
def manifest():
    return send_from_directory(
        current_app.static_folder, "manifest.json", mimetype="application/manifest+json"
    )


@routes_bp.route("/service-worker.js")
def service_worker():
    return send_from_directory(
        current_app.static_folder, "service-worker.js", mimetype="application/javascript"
    )


@routes_bp.route("/dashboard")
@login_required
def dashboard():
    user = db.session.get(User, session["user_id"])

    recent = (
        AuditLog.query.filter_by(user_id=user.id)
        .order_by(AuditLog.timestamp.desc())
        .limit(5)
        .all()
    )

    return render_template("dashboard.html", user=user, recent_activity=recent)


@routes_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = db.session.get(User, session["user_id"])

    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not valid_email(email):
            flash("Invalid email")
            return redirect(url_for("routes.settings"))

        if email != user.email:
            if User.query.filter_by(email=email).first():
                flash("Email already in use.", "danger")
            else:
                user.email = email
                db.session.commit()
                flash("Email updated successfully.", "success")

        return redirect(url_for("routes.settings"))

    return render_template("settings.html", user=user)


@routes_bp.route("/api/face/status")
@login_required
def face_status():
    user = db.session.get(User, session["user_id"])
    return jsonify({"enrolled": user.face_enrolled})


@routes_bp.route("/api/face/check-user")
@limiter.limit("20 per minute")
def face_check_user():
    # No revela si el usuario existe o no (mismo shape de respuesta en ambos
    # casos) para evitar enumeración de cuentas (ISO 27001 A.8.5).
    username = request.args.get("username", "").strip()

    if not username:
        return jsonify({"enrolled": False})

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"enrolled": False})

    return jsonify({"enrolled": bool(user.face_enrolled)})


@routes_bp.route("/api/face/enroll", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
def face_enroll():
    from .face_service import enroll_faces

    data = request.get_json()

    if not data or "images" not in data or not data["images"]:
        return jsonify({"error": "No images provided"}), 400

    try:
        enroll_faces(session["username"], data["images"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Enrollment failed"}), 500

    user = db.session.get(User, session["user_id"])
    user.face_enrolled = True

    db.session.add(
        AuditLog(
            user_id=user.id,
            action="face_enroll",
            ip_address=request.remote_addr,
            success=True,
        )
    )
    db.session.commit()

    return jsonify({"enrolled": True}), 200


@routes_bp.route("/api/face/verify", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
def face_verify():
    from .face_service import verify_face_detailed

    data = request.get_json()

    if not data or "image" not in data:
        return jsonify({"error": "No image provided"}), 400

    try:
        result = verify_face_detailed(session["username"], data["image"])

        if result["verified"]:
            db.session.add(
                AuditLog(
                    user_id=session["user_id"],
                    action="face_login",
                    ip_address=request.remote_addr,
                    success=True
                )
            )
            db.session.commit()
            return jsonify(result), 200

        return jsonify(result), 401

    except Exception:
        return jsonify({"error": "Internal error"}), 500


@routes_bp.route("/api/face/login-verify", methods=["POST"])
@limiter.limit("3 per minute")
def face_login_verify():
    from .face_service import verify_face_detailed

    data = request.get_json()

    if not data or "username" not in data or "image" not in data:
        return jsonify({"error": "Username and image required"}), 400

    username = data["username"].strip()

    if not username:
        return jsonify({"error": "Username required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.face_enrolled:
        return jsonify({"error": "Face login not enrolled"}), 400

    try:
        result = verify_face_detailed(username, data["image"])

        if result["verified"]:
            session.clear()
            session.permanent = True
            session["user_id"] = user.id
            session["username"] = user.username

            db.session.add(
                AuditLog(
                    user_id=user.id,
                    action="face_login",
                    ip_address=request.remote_addr,
                    success=True
                )
            )
            db.session.commit()

            return jsonify(result), 200

        return jsonify(result), 401

    except Exception:
        return jsonify({"error": "Internal error"}), 500


# Los siguientes son endpoints JSON consumidos por fetch()/la app móvil, no por
# formularios HTML con sesión de navegador clásica: no envían el token CSRF de
# Flask-WTF. Quedan exentos de CSRF y se apoyan en:
#   - login_required (sesión) donde aplica,
#   - rate limiting por endpoint,
#   - cookies SameSite=Lax + HttpOnly (ver config.py) como mitigación de CSRF.
csrf.exempt(face_status)
csrf.exempt(face_check_user)
csrf.exempt(face_enroll)
csrf.exempt(face_verify)
csrf.exempt(face_login_verify)
