import os
import requests
from flask import Blueprint, redirect, url_for, session, flash, request

auth = Blueprint('auth', __name__)

# Load secrets 
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
SCOPE = ["User.Read"]

@auth.route("/login")
def microsoft_login():
    if "user" in session:
        #print("[DEBUG] User already in session, redirecting to dashboard...")
        return redirect(url_for("admin.dashboard"))  # Prevents re-login loop

    #print("[DEBUG] Redirecting user to Microsoft login...")
    login_url = (
        f"{AUTHORITY}?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&scope={' '.join(SCOPE)}"
    )
    return redirect(login_url)


@auth.route('/auth/callback')
def microsoft_callback():
    # Get the authorization code from Microsoft response
    code = request.args.get("code")
    if not code:
        flash("Login failed. No authorization code received.", "error")
        return redirect(url_for('main.home'))

    # Exchange code for access token
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPE),
    }
    response = requests.post(TOKEN_URL, data=token_data)
    token_json = response.json()

    if "access_token" not in token_json:
        flash("Failed to authenticate with Microsoft.", "error")
        return redirect(url_for('main.home'))

    # Store token & user session
    access_token = token_json["access_token"]
    session["access_token"] = access_token

    # Get user info
    user_info = requests.get("https://graph.microsoft.com/v1.0/me", headers={"Authorization": f"Bearer {access_token}"}).json()

    session["user"] = user_info.get("displayName", "Unknown User")
    session["email"] = user_info.get("mail", "No Email Provided")

    #  Assign admin role if email matches yours
    if session["email"].lower() == "hkliu@cougarnet.uh.edu":
        session["role"] = "Admin"
    else:
        session["role"] = "User"

    flash(f"Welcome, {session['user']}!", "success")
    return redirect(url_for('admin.dashboard'))

@auth.route('/logout')
def logout():
    session.clear()
    print("[DEBUG] User session cleared")
    flash("You have been logged out.", "success")
    return redirect(url_for('main.home'))
