from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Department

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_view"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html")

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password. Please check your credentials.", "danger")
            return render_template("login.html")

        if not user.is_active:
            flash("Your account has been deactivated. Please contact an administrator.", "warning")
            return render_template("login.html")

        login_user(user, remember=remember)
        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("dashboard.dashboard_view")

        flash(f"Welcome back, {user.username}!", "success")
        return redirect(next_page)

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_view"))

    departments = Department.query.order_by(Department.name.asc()).all()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        dept_id = request.form.get("department_id")

        if not username or not email or not password:
            flash("All required fields must be filled.", "danger")
            return render_template("register.html", departments=departments)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html", departments=departments)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html", departments=departments)

        if User.query.filter_by(username=username).first():
            flash("Username already taken. Please choose another.", "danger")
            return render_template("register.html", departments=departments)

        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists.", "danger")
            return render_template("register.html", departments=departments)

        dept_val = int(dept_id) if dept_id and dept_id.isdigit() else None

        new_user = User(
            username=username,
            email=email,
            role="user",
            department_id=dept_val,
            is_active=True
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! You may now sign in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {str(e)}", "danger")

    return render_template("register.html", departments=departments)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("auth.login"))


# JSON API Endpoints
@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"success": False, "error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"success": False, "error": "Account deactivated"}), 403

    login_user(user, remember=True)
    return jsonify({"success": True, "user": user.to_dict()})


@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    dept_id = data.get("department_id")

    if not username or not email or not password:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"success": False, "error": "User with this username or email already exists"}), 409

    user = User(username=username, email=email, role="user", department_id=dept_id, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user)
    return jsonify({"success": True, "user": user.to_dict()}), 201


@auth_bp.route("/api/auth/me", methods=["GET"])
def api_me():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False}), 401
    return jsonify({"authenticated": True, "user": current_user.to_dict()})
