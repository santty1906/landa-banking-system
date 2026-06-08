import json
import os

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .models import AuditLog, User, db
from .security import login_required

routes_bp = Blueprint("routes", __name__, template_folder="templates")


@routes_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("routes.dashboard"))
    return redirect(url_for("auth.login"))


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
        if email and email != user.email:
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


@routes_bp.route("/api/face/enroll", methods=["POST"])
@login_required
def face_enroll():
    from .face_service import enroll_faces

    user = db.session.get(User, session["user_id"])

    data = request.get_json()
    if not data or "images" not in data:
        return jsonify({"error": "No images provided"}), 400

    try:
        enroll_faces(session["username"], data["images"])
        user.face_enrolled = True
        db.session.commit()
        return jsonify({"message": "Face enrolled successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Enrollment failed: {str(e)}"}), 500


@routes_bp.route("/api/face/verify", methods=["POST"])
@login_required
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
                    success=True,
                )
            )
            db.session.commit()
            return jsonify(result), 200
        return jsonify(result), 401
    except Exception as e:
        return jsonify({"error": f"Verification failed: {str(e)}"}), 500


@routes_bp.route("/api/face/login-verify", methods=["POST"])
def face_login_verify():
    from .face_service import verify_face_detailed

    data = request.get_json()
    if not data or "image" not in data or "username" not in data:
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
            session["user_id"] = user.id
            session["username"] = user.username
            db.session.add(
                AuditLog(
                    user_id=user.id,
                    action="face_login",
                    ip_address=request.remote_addr,
                    success=True,
                )
            )
            db.session.commit()
            return jsonify(result), 200
        return jsonify(result), 401
    except Exception as e:
        return jsonify({"error": f"Verification failed: {str(e)}"}), 500


@routes_bp.route("/api/face/check-user")
def face_check_user():
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"enrolled": False})
    user = User.query.filter_by(username=username).first()
    if user and user.face_enrolled:
        return jsonify({"enrolled": True, "username": user.username})
    return jsonify({"enrolled": False})


@routes_bp.route("/offline")
def offline():
    return render_template("offline.html")


@routes_bp.route("/manifest.json")
def manifest():
    return current_app.send_static_file("manifest.json")


@routes_bp.route("/service-worker.js")
def service_worker():
    return current_app.send_static_file("service-worker.js")
