from flask import Blueprint, render_template, session, redirect, url_for, flash, request, current_app, send_file
from werkzeug.utils import secure_filename
import os
import app.services.academic_service as academic_service
from app.models import User, AcademicRequests
from app.decorators import active_required
from datetime import datetime
from app import db
import subprocess
import shutil


dashboard = Blueprint("dashboard", __name__)

@dashboard.route("/dashboard")
@active_required
def user_dashboard():

    academic_requests = AcademicRequests.query.filter_by(email=session.get("email")).all()
    return render_template("dashboard.html", user = session["user"], email = session["email"], role = session["role"], academic_requests = academic_requests)

@dashboard.route("/dashboard/request_form")
@active_required
def request_form():
    # Get the form_id from query string parameters
    form_id = request.args.get("form_id", type=int)
    # For now, simply flash a message and render a simple template.
    if form_id == 1:
        flash("Special Circumstance Form Requested", "info")
        return redirect(url_for("dashboard.special_circumstance"))
    elif form_id == 2:
        flash("Instructor-Initiated Drop Form Requested", "info")
        return redirect(url_for("dashboard.course_drop"))
    else:
        flash("Invalid form selection", "error")
    # In a full implementation, you could pre-fill a form with user data or redirect to a dedicated form page.
    return redirect(url_for("dashboard.dashboard_home"))

@dashboard.route("/special_circumstance", methods=["GET", "POST"])
@active_required
def special_circumstance():
    if request.method == "POST":
        # Retrieve form values
        student_name = request.form.get("student_name")
        student_id = request.form.get("student_id")
        degree = request.form.get("degree")
        graduation_date = request.form.get("graduation_date")
        special_request_option = request.form.get("special_request_option")
        other_option_detail = request.form.get("other_option_detail")
        justification = request.form.get("justification")
        date = datetime.now().strftime("%m-%d-%Y")

        signature_file = request.files.get("signature")
        signature_filename = None
        if signature_file:
            from werkzeug.utils import secure_filename
            # Optionally, validate file extension if needed
            signature_filename = secure_filename(signature_file.filename)
            # Save file to 'app/static/uploads' folder (ensure the folder exists)
            upload_folder = os.path.join("app", "static", "uploads")
            # Create the folder if it doesn't exist
            os.makedirs(upload_folder, exist_ok=True)
            upload_path = os.path.join(upload_folder, signature_filename)
            signature_file.save(upload_path)

        request_data = {
            "student_name": student_name,
            "student_id": student_id,
            "degree": degree,
            "graduation_date": graduation_date,
            "special_request_option": special_request_option,
            "other_option_detail": other_option_detail,
            "justification": justification,
            "date": date,
            "signature": signature_filename  # store file name
        }

        # Determine whether to save as draft or submit
        action = request.form.get("action")
        if action == "save_draft":
            status = "draft"
        else:
            status = "under_review"  # or "pending", as per your business logic

        academic_service.submit_form(request_data, 1, status)
        flash("Draft saved successfully." if status == "draft" else "Form submitted successfully.", "success")
        return redirect(url_for("dashboard.user_dashboard"))

    return render_template("special_circumstance.html", current_date=datetime.now().strftime("%m-%d-%Y"))



@dashboard.route("/special_circumstance/edit/<int:request_id>", methods=["GET", "POST"])
@active_required
def special_circumstance_edit(request_id):
    draft = AcademicRequests.query.filter_by(id=request_id, email=session.get("email")).first_or_404()
    if request.method == "POST":
        draft["student_name"] = request.form.get("student_name")
        draft["student_id"] = request.form.get("student_id")
        draft["degree"] = request.form.get("degree")
        draft["graduation_date"] = request.form.get("graduation_date")
        draft["special_request_option"] = request.form.get("special_request_option")
        draft["other_option_detail"] = request.form.get("other_option_detail")
        draft["justification"] = request.form.get("justification")

        # Process new signature file upload if provided
        signature_file = request.files.get("signature")
        if signature_file:
            from werkzeug.utils import secure_filename
            signature_filename = secure_filename(signature_file.filename)
            upload_folder = os.path.join("app", "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            signature_file.save(os.path.join(upload_folder, signature_filename))
            draft["signature_filename"] = signature_filename

        academic_service.update_form(id, draft)
        flash("Form updated succesfully.", "success")

    return render_template("special_circumstance.html")


@dashboard.route("/dashboard/special_circumstance/edit/<int:request_id>", methods=["GET", "POST"])
@active_required
def special_circumstance_edit_dashboard(request_id):
    if request.method == "POST":
        draft["student_name"] = request.form.get("student_name")
        draft["student_id"] = request.form.get("student_id")
        draft["course_subject"] = request.form.get("course_subject")
        draft["course_number"] = request.form.get("course_number")
        draft["semester"] = request.form.get("semester")
        draft["year"] = request.form.get("year")

        # Process new signature file upload if provided
        signature_file = request.files.get("signature")
        if signature_file:
            from werkzeug.utils import secure_filename
            signature_filename = secure_filename(signature_file.filename)
            upload_folder = os.path.join("app", "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            signature_file.save(os.path.join(upload_folder, signature_filename))
            draft["signature_filename"] = signature_filename

        academic_service.update_form(id, draft)
        flash("Form updated succesfully.", "success")

    return render_template("special_circumstance.html")


#TODO: Change the endpoints
@dashboard.route("/course_drop", methods=["GET", "POST"])
@active_required
def course_drop():
    if request.method == "POST":
        # Retrieve form values
        student_name = request.form.get("student_name")
        student_id = request.form["student_id"]
        semester = request.form["semester"]
        year = request.form["year"]
        subject = request.form["subject"]
        catalog_number = request.form["catalog_number"]
        class_number = request.form["class_number"]
        date = datetime.now().strftime("%m-%d-%Y")

        # Handle Signature Upload (Like Special Circumstance)
        signature_file = request.files.get("signature")
        signature_filename = None
        if signature_file:
            from werkzeug.utils import secure_filename
            signature_filename = secure_filename(signature_file.filename)
            upload_folder = os.path.join("app", "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            upload_path = os.path.join(upload_folder, signature_filename)
            signature_file.save(upload_path)

        # Prepare request data for storage
        request_data = {
            "student_name": student_name,
            "student_id": student_id,
            "semester": semester,
            "year": year,
            "subject": subject,
            "catalog_number": catalog_number,
            "class_number": class_number,
            "date": date,
            "signature": signature_filename,  # Store uploaded signature filename
        }

        # Determine if it's a draft or submitted form
        action = request.form.get("action")
        status = "draft" if action == "save_draft" else "under_review"

        # Save form data (store in the database)
        academic_service.submit_form(request_data, 2, status)

        flash("Draft saved successfully." if status == "draft" else "Form submitted successfully.", "success")
        return redirect(url_for("dashboard.user_dashboard"))

    return render_template("course_drop.html", current_date=datetime.now().strftime("%m-%d-%Y"))


@dashboard.route("/course_drop/edit/<int:request_id>", methods=["GET", "POST"])
@active_required
def course_drop_edit(request_id):
    draft = AcademicRequests.query.filter_by(id=request_id, email=session.get("email")).first_or_404()
    if request.method == "POST":
        # Retrieve existing draft and update values
        draft["student_name"] = request.form.get("student_name")
        draft["student_id"] = request.form["student_id"]
        draft["semester"] = request.form["semester"]
        draft["year"] = request.form["year"]
        draft["subject"] = request.form["subject"]
        draft["catalog_number"] = request.form["catalog_number"]
        draft["class_number"] = request.form["class_number"]

        # Handle Signature Upload
        signature_file = request.files.get("signature")
        if signature_file:
            from werkzeug.utils import secure_filename
            signature_filename = secure_filename(signature_file.filename)
            upload_folder = os.path.join("app", "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            signature_file.save(os.path.join(upload_folder, signature_filename))
            draft["signature_filename"] = signature_filename

        academic_service.update_form(request_id, draft)
        flash("Form updated successfully.", "success")

    return render_template("course_drop.html")

@dashboard.route("/dashboard/course_drop/edit/<int:request_id>", methods=["GET", "POST"])
@active_required
def course_drop_edit_dashboard(request_id):
    if request.method == "POST":
        draft["student_name"] = request.form.get("student_name")
        draft["student_id"] = request.form["student_id"]
        draft["semester"] = request.form["semester"]
        draft["year"] = request.form["year"]
        draft["subject"] = request.form["subject"]
        draft["catalog_number"] = request.form["catalog_number"]
        draft["class_number"] = request.form["class_number"]

        # Handle Signature Upload
        signature_file = request.files.get("signature")
        if signature_file:
            from werkzeug.utils import secure_filename
            signature_filename = secure_filename(signature_file.filename)
            upload_folder = os.path.join("app", "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            signature_file.save(os.path.join(upload_folder, signature_filename))
            draft["signature_filename"] = signature_filename

        academic_service.update_form(request_id, draft)
        flash("Form updated successfully.", "success")

    return render_template("course_drop.html")



@dashboard.route("/dashboard/delete_form/<int:request_id>", methods=["POST"])
@active_required
def delete_form(request_id):
    # Query for the request; ensure it belongs to the logged-in student
    draft = AcademicRequests.query.filter_by(id=request_id, email=session.get("email")).first_or_404()
    
    # Delete the draft and commit changes
    db.session.delete(draft)
    db.session.commit()
    
    flash("Your request has been deleted.", "success")
    return redirect(url_for("dashboard.user_dashboard"))


@dashboard.route("/dashboard/view_pdf/<int:request_id>", methods=["GET"])
@active_required
def view_pdf(request_id):
    draft = AcademicRequests.query.filter_by(id=request_id, email=session.get("email")).first_or_404()
    temp_dir = os.path.join(current_app.instance_path, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    if draft.form_type == 1: 
        rendered_tex = render_template("special_circumstance.tex.j2", request_data=draft.data)
        tex_file = os.path.join(temp_dir, "special_circumstance.tex")
        pdf_file = os.path.join(temp_dir, "special_circumstance.pdf")
    else:
        rendered_tex = render_template("course_drop.tex.j2", request_data=draft.data)
        tex_file = os.path.join(temp_dir, "course_drop.tex")
        pdf_file = os.path.join(temp_dir, "course_drop.pdf")

    # Create a temporary directory to store the .tex and .pdf files
    
    
    # Write the rendered LaTeX to a file
    with open(tex_file, "w") as f:
        f.write(rendered_tex)
    
    # Compile the .tex file into a PDF using pdflatex.
    try:
        makefile_src = os.path.join(current_app.root_path, "latex", "Makefile")
        makefile_dst = os.path.join(temp_dir, "Makefile")
        shutil.copy(makefile_src, makefile_dst)
        subprocess.run(["make", "-C", temp_dir, "clean"], check=True)
        if draft.form_type == 2:
            subprocess.run(["make", "-C", temp_dir, "course_drop.pdf"], check=True)
            subprocess.run(["make", "-C", temp_dir, "course_drop.pdf"], check=True)
        else:
            subprocess.run(["make", "-C", temp_dir, "special_circumstance.pdf"], check=True)
            subprocess.run(["make", "-C", temp_dir, "special_circumstance.pdf"], check=True)
    except subprocess.CalledProcessError as e:
        flash("Error generating PDF.", "error")
        return redirect(url_for("dashboard.user_dashboard"))
    
    # Return the generated PDF as a response.
    return send_file(pdf_file, mimetype="application/pdf", as_attachment=False)

