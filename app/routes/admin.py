from flask import Blueprint, render_template, session, redirect, url_for, flash

admin = Blueprint("admin", __name__)

@admin.route("/dashboard")
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
