from flask import Blueprint, render_template, session, redirect, url_for, flash
import app.services.user_services as user_service

admin = Blueprint("admin", __name__)

@admin.route("/admin/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please log in to access the dashboard", "error")
        return redirect(url_for("auth.microsoft_login"))

    # Restrict access to Admins only
    if session.get("role") != "Admin":
        flash("Access Denied: Admins Only!", "error")
        return redirect(url_for("main.home"))

    # Temporary Hardcoded Users (Replace with Database Query Later)
    users = [
        {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "User", "status": "Active"},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "Admin", "status": "Active"},
    ]

    return render_template("admin.html", user=session["user"], email=session["email"], role=session["role"], users=users)


@admin.route("/admin/update_user")
def update_user():
    pass

@admin.route("/admin/delete_user")
def delete_user():
    pass

@admin.route("/admin/create_user")
def create_user():
    pass

