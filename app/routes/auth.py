import os
import requests
from flask import Blueprint, redirect, url_for, session, flash, request, render_template
from app.models import User
import app.services.auth_service as auth_service
from app.extensions.db import db

auth = Blueprint('auth', __name__)

# Load secrets 
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
SCOPE = ["User.Read"]

@auth.route("/login", methods = ["GET", "POST"])
def microsoft_login():
    if "user" in session:
        role = session.get("role")
        if role == User.ROLE_ADMIN:
            return redirect(url_for("admin.admin_dashboard"))
        elif role in [User.ROLE_DEPARTMENT_COUNSELOR, User.ROLE_ACADEMIC_DIRECTOR, User.ROLE_COLLEGE_SUPERVISOR]:
            return redirect(url_for("approval.approval_dashboard"))
        else:
            return redirect(url_for("dashboard.user_dashboard"))

    redirect_uri = url_for('auth.microsoft_callback', _external=True)
    login_url = (
        f"{AUTHORITY}?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={redirect_uri}"
        f"&scope={' '.join(SCOPE)}"
    )
    return redirect(login_url)


@auth.route('/complete-profile', methods=['GET', 'POST'])
def complete_profile():
    user_id = session.get("user_id")
    user = User.query.filter_by(email=session["email"].lower()).first()

    # POST will come from our JS-prompt form
    if request.method == 'POST':
        entered = request.form.get('uh_id', '').strip()
        # 1) they clicked “Cancel” or left blank?
        if not entered:
            return redirect(url_for('auth.logout'))

        # 2) if they already had uh_id in DB, verify it
        if user.uh_id:
            if str(user.uh_id) != entered:
                flash("UH ID mismatch – logging you out.", "error")
                return redirect(url_for('auth.logout'))
        else:
            # first-time: assign it
            user.uh_id = int(entered)
            db.session.commit()
        

        # success!
        session["role"] = user.role
        session["uh_id"] = user.uh_id
        session["exists"] = True
        session["active"] = True
    
        # Redirect based on role
        if user.role == User.ROLE_ADMIN:
            return redirect(url_for('admin.admin_dashboard'))
        elif user.role in [User.ROLE_DEPARTMENT_COUNSELOR, User.ROLE_ACADEMIC_DIRECTOR, User.ROLE_COLLEGE_SUPERVISOR]:
            return redirect(url_for('approval.approval_dashboard'))
        else:
            return redirect(url_for('dashboard.user_dashboard'))

    # GET just renders our “hidden” prompt page
    return render_template('complete_profile.html')



@auth.route('/auth/callback')
def microsoft_callback():
    redirect_uri = url_for('auth.microsoft_callback', _external=True)
    user, err_msg = auth_service.microsoft_callback(redirect_uri)

    if type(user) is not type(dict()):
        flash(err_msg, "error")
        return redirect(url_for("main.home"))

    user = User.query.filter_by(email=session["email"].lower()).first()

    if user is None:
        flash("Account doesn't exist in the system. Please logout and login with a valid account or contact support", "error")
        session["exists"] = False
        return redirect(url_for('main.home'))

    if user.status.lower() != "active":
        flash("Account isn't active. Please logout and login with a valid account or contact support", "error")
        session["active"] = False
        return redirect(url_for("main.home"))

    flash("We need your UH ID to finish logging you in.", "warning")
    return redirect(url_for('auth.complete_profile'))

    flash(f"Welcome, {session['user']}!", "success")
    
    # Set the session role to the actual user role from the database
    session["role"] = user.role
    
    # Redirect based on role
    if user.role == User.ROLE_ADMIN:
        return redirect(url_for('admin.admin_dashboard'))
    elif user.role in [User.ROLE_DEPARTMENT_COUNSELOR, User.ROLE_ACADEMIC_DIRECTOR, User.ROLE_COLLEGE_SUPERVISOR]:
        return redirect(url_for('approval.approval_dashboard'))
    else:
        return redirect(url_for('dashboard.user_dashboard'))


@auth.route('/logout')
def logout():
    session.clear()
    ms_logout_url = "https://login.microsoftonline.com/common/oauth2/logout?post_logout_redirect_uri=" + url_for('main.home', _external=True)
    flash("You have been logged out.", "success")
    return redirect(ms_logout_url)


# New user registration route
@auth.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        display_name = request.form.get("display_name")
        email = request.form.get("email")
        uh_id = request.form.get("uhid")

        if not email.endswith("@cougarnet.uh.edu"):
            flash("Only UH emails are allowed.", "error")
            return render_template("register.html")

        # Check if user exists already
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with that email already exists.", "error")
            return render_template("register.html")

        new_user = User(user_id = uh_id,display_name=display_name, email=email.lower(), role=User.ROLE_USER, status="active")
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for("auth.microsoft_login"))

    return render_template("register.html")
