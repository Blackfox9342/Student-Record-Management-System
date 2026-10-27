from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from app.models import User

auth_bp = Blueprint("auth", __name__)

ROLE_DASHBOARD = {
    "admin": "main.admin_dashboard",
    "student": "main.student_dashboard",
    "faculty": "main.faculty_dashboard",
}


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role", "student")

    if current_user.is_authenticated:
        return redirect(url_for(ROLE_DASHBOARD.get(current_user.role, "main.home")))

    if request.method == "POST":
        role = request.form.get("role", role)
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email, role=role).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Welcome, {user.full_name}.", "success")
            return redirect(url_for(ROLE_DASHBOARD.get(user.role, "main.home")))

        flash("Invalid credentials for the selected portal.", "danger")

    return render_template("login.html", active_role=role)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.home"))
