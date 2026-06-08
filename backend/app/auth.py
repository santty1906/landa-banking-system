from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .models import AuditLog, User, db
from .security import hash_password, verify_password

auth_bp = Blueprint("auth", __name__, template_folder="templates")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please fill in all fields.", "danger")
            return render_template("login.html")

        user = User.query.filter_by(username=username).first()

        if user and verify_password(password, user.password_hash):
            session["user_id"] = user.id
            session["username"] = user.username
            db.session.add(
                AuditLog(
                    user_id=user.id,
                    action="login",
                    ip_address=request.remote_addr,
                    success=True,
                )
            )
            db.session.commit()
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for("routes.dashboard"))

        db.session.add(
            AuditLog(
                action=f"failed login for {username}",
                ip_address=request.remote_addr,
                success=False,
            )
        )
        db.session.commit()
        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password or not confirm:
            flash("Please fill in all fields.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    if "user_id" in session:
        db.session.add(
            AuditLog(
                user_id=session["user_id"],
                action="logout",
                ip_address=request.remote_addr,
                success=True,
            )
        )
        db.session.commit()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
