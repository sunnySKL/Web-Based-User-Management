@dashboard.route("/dashboard")
@active_required
def user_dashboard():
    # Get academic requests and order them by ID in descending order
    academic_requests = AcademicRequests.query.filter_by(email=session.get("email")).order_by(AcademicRequests.id.desc()).all()
    return render_template("dashboard.html", user = session["user"], email = session["email"], role = session["role"], academic_requests = academic_requests) 