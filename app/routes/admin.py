from flask import Blueprint, render_template, session, redirect, url_for, flash

admin = Blueprint("admin", __name__)

@admin.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.microsoft_login"))

    #  Restrict access to Admins
    if session.get("role") != "Admin":
        flash("Access Denied: Admins Only!", "error")
        return redirect(url_for("main.home"))

    users = [
        {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "User"},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "Admin"},
    ]

    return render_template("dashboard.html", user=session["user"], email=session["email"], role=session["role"], users=users)
