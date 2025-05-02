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
import base64
from io import BytesIO
import uuid


dashboard = Blueprint("dashboard", __name__)

@dashboard.route("/dashboard")
@active_required
def user_dashboard():
    # Get academic requests and order them by ID in descending order
    academic_requests = AcademicRequests.query.filter_by(email=session.get("email")).order_by(AcademicRequests.id.desc()).all()
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
    elif form_id == 3:
        flash("Affidavit of Intent to Become a Permanent Resident Requested", "info")
        return redirect(url_for("dashboard.affidavit_intent"))
    elif form_id == 4:
        flash("Tuition Exemption Request Form Requested", "info")
        return redirect(url_for("dashboard.tuition_exemption"))
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
        signature_base64 = None
        if signature_file and signature_file.filename != "":
            # Read binary data before saving the file
            binary_data = signature_file.read()
            # Convert binary data to base64 encoded string
            signature_base64 = base64.b64encode(binary_data).decode('utf-8')
            
            # Reset file pointer to beginning of file
            signature_file.seek(0)
            
            # Save file to 'app/static/uploads' folder
            from werkzeug.utils import secure_filename
            signature_filename = secure_filename(signature_file.filename)
            upload_folder = os.path.join("app", "static", "uploads")
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
            "signature": signature_base64  # store base64 encoded signature
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
            
            # Read binary data
            binary_data = signature_file.read()
            # Convert binary data to base64 encoded string
            signature_base64 = base64.b64encode(binary_data).decode('utf-8')
            draft["signature"] = signature_base64

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

        # Handle Signature Upload
        signature_file = request.files.get("signature")
        signature_base64 = None
        if signature_file and signature_file.filename != "":
            # Read binary data before saving the file
            binary_data = signature_file.read()
            # Convert binary data to base64 encoded string
            signature_base64 = base64.b64encode(binary_data).decode('utf-8')
            
            # Reset file pointer to beginning of file
            signature_file.seek(0)
            
            # Save file to uploads folder
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
            "signature": signature_base64,  # Store base64 encoded signature
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

            # Read binary data
            binary_data = signature_file.read()
            # Convert binary data to base64 encoded string
            signature_base64 = base64.b64encode(binary_data).decode('utf-8')
            draft["signature"] = signature_base64

        academic_service.update_form(request_id, draft)
        flash("Form updated successfully.", "success")

    return render_template("course_drop.html")



@dashboard.route("/dashboard/delete_form/<int:request_id>", methods=["POST"])
@active_required
def delete_form(request_id):
    """Delete a form/request"""
    try:
        # Query for the request; ensure it belongs to the logged-in student
        draft = AcademicRequests.query.filter_by(id=request_id, email=session.get("email")).first_or_404()
        
        # First, try to delete any approval logs manually with raw SQL
        # This is a workaround for the case where the approval_logs table doesn't exist yet
        try:
            # Use raw SQL to delete any related approval logs first
            sql = "DELETE FROM approval_logs WHERE request_id = :request_id"
            db.session.execute(sql, {"request_id": request_id})
            db.session.commit()
        except Exception as log_error:
            # Ignore errors related to missing table - we'll proceed with deleting the request
            db.session.rollback()
            current_app.logger.warning(f"Could not delete approval logs: {log_error}")
        
        # Now delete the request
        db.session.delete(draft)
        db.session.commit()
        
        flash("Your request has been deleted.", "success")
    except Exception as e:
        # Log the error and rollback the transaction
        current_app.logger.error(f"Error deleting request {request_id}: {e}")
        db.session.rollback()
        
        # For this specific error, try another approach
        if "relation \"approval_logs\" does not exist" in str(e):
            try:
                # Try direct SQL delete which doesn't trigger the ORM relationship
                sql = "DELETE FROM academic_requests WHERE id = :id AND email = :email"
                result = db.session.execute(sql, {"id": request_id, "email": session.get("email")})
                db.session.commit()
                
                if result.rowcount > 0:
                    flash("Your request has been deleted.", "success")
                    return redirect(url_for("dashboard.user_dashboard"))
                else:
                    flash("Request not found or you don't have permission to delete it.", "error")
            except Exception as direct_error:
                db.session.rollback()
                current_app.logger.error(f"Error with direct SQL delete: {direct_error}")
                flash(f"Could not delete the request. Please contact support.", "error")
        else:
            flash(f"An error occurred while deleting the request. Please try again later.", "error")
    
    return redirect(url_for("dashboard.user_dashboard"))


@dashboard.route("/dashboard/view_pdf/<int:request_id>", methods=["GET"])
@active_required
def view_pdf(request_id):
    draft = AcademicRequests.query.filter_by(id=request_id, email=session.get("email")).first_or_404()
    request_data = draft.data.copy()
    temp_dir = os.path.join(current_app.instance_path, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Debug prints
    print("Request data keys:", request_data.keys())
    
    # Handle signature if it exists
    if "signature" in request_data and request_data["signature"]:
        print("Signature found in request data")
        # Create a unique filename for this signature
        signature_image_filename = f"signature_{request_id}.png"
        signature_image_path = os.path.join(temp_dir, signature_image_filename)
        
        try:
            # Remove file if it already exists
            if os.path.exists(signature_image_path):
                os.remove(signature_image_path)
                
            # Decode the Base64 string into binary data
            signature_binary = base64.b64decode(request_data["signature"])
            print(f"Decoded signature length: {len(signature_binary)} bytes")
            
            # Write image data to file
            with open(signature_image_path, "wb") as img_file:
                img_file.write(signature_binary)
            
            print(f"Signature saved to: {signature_image_path}")
            
            # Set the image path for the template - just use the filename, not the full path
            request_data["signature_image_filename"] = signature_image_filename
        except Exception as e:
            current_app.logger.error(f"Error processing signature image: {e}")
            print(f"Error processing signature: {e}")
            request_data["signature_image_filename"] = None
    else:
        print("No signature data found in the request")
        request_data["signature_image_filename"] = None

    # Copy signature to LaTeX working directory if it exists
    if request_data["signature_image_filename"]:
        # Ensure the signature is in the same directory as the .tex file for simpler inclusion
        signature_source = os.path.join(temp_dir, request_data["signature_image_filename"])
        if os.path.exists(signature_source):
            print(f"File exists at {signature_source}")
        else:
            print(f"File does not exist: {signature_source}")

    # Generate appropriate template based on form type
    if draft.form_type == 1: 
        rendered_tex = render_template("special_circumstance.tex.j2", request_data=request_data)
        tex_file = os.path.join(temp_dir, "special_circumstance.tex")
        pdf_file = os.path.join(temp_dir, "special_circumstance.pdf")
    elif draft.form_type == 2:
        rendered_tex = render_template("course_drop.tex.j2", request_data=request_data)
        tex_file = os.path.join(temp_dir, "course_drop.tex")
        pdf_file = os.path.join(temp_dir, "course_drop.pdf")
    elif draft.form_type == 3:
        rendered_tex = render_template("affidavit_intent.tex.j2", request_data=request_data)
        tex_file = os.path.join(temp_dir, "affidavit_intent.tex")
        pdf_file = os.path.join(temp_dir, "affidavit_intent.pdf")
    elif draft.form_type == 4:
        rendered_tex = render_template("tuition_exemption.tex.j2", request_data=request_data)
        tex_file = os.path.join(temp_dir, "tuition_exemption.tex")
        pdf_file = os.path.join(temp_dir, "tuition_exemption.pdf")
    else:
        rendered_tex = render_template("course_drop.tex.j2", request_data=request_data)
        tex_file = os.path.join(temp_dir, "course_drop.tex")
        pdf_file = os.path.join(temp_dir, "course_drop.pdf")
        
    # Write the rendered LaTeX to a file
    with open(tex_file, "w") as f:
        f.write(rendered_tex)
    
    # Print LaTeX content for debugging
    print("Generated LaTeX content:")
    print(rendered_tex[:200] + "...")
    
    # Compile the .tex file into a PDF using pdflatex.
    try:
        makefile_src = os.path.join(current_app.root_path, "latex", "Makefile")
        makefile_dst = os.path.join(temp_dir, "Makefile")
        shutil.copy(makefile_src, makefile_dst)
        
        # Run compilation commands
        print("Running make clean")
        subprocess.run(["make", "-C", temp_dir, "clean"], check=True)
        
        if draft.form_type == 2:
            print("Compiling course_drop.pdf")
            result = subprocess.run(["make", "-C", temp_dir, "course_drop.pdf"], check=True, capture_output=True, text=True)
            print(f"Compilation output: {result.stdout}")
            if result.stderr:
                print(f"Compilation errors: {result.stderr}")
                
            # Run twice for references
            subprocess.run(["make", "-C", temp_dir, "course_drop.pdf"], check=True)
        elif draft.form_type == 3:
            print("Compiling affidavit_intent.pdf")
            result = subprocess.run(["make", "-C", temp_dir, "affidavit_intent.pdf"], check=True, capture_output=True, text=True)
            print(f"Compilation output: {result.stdout}")
            if result.stderr:
                print(f"Compilation errors: {result.stderr}")
                
            # Run twice for references
            subprocess.run(["make", "-C", temp_dir, "affidavit_intent.pdf"], check=True)
        elif draft.form_type == 4:
            print("Compiling tuition_exemption.pdf")
            result = subprocess.run(["make", "-C", temp_dir, "tuition_exemption.pdf"], check=True, capture_output=True, text=True)
            print(f"Compilation output: {result.stdout}")
            if result.stderr:
                print(f"Compilation errors: {result.stderr}")
                
            # Run twice for references
            subprocess.run(["make", "-C", temp_dir, "tuition_exemption.pdf"], check=True)
        else:
            print("Compiling special_circumstance.pdf")
            result = subprocess.run(["make", "-C", temp_dir, "special_circumstance.pdf"], check=True, capture_output=True, text=True)
            print(f"Compilation output: {result.stdout}")
            if result.stderr:
                print(f"Compilation errors: {result.stderr}")
                
            # Run twice for references
            subprocess.run(["make", "-C", temp_dir, "special_circumstance.pdf"], check=True)
            
        print("PDF compilation completed successfully")
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"Error compiling PDF: {e}")
        print(f"PDF compilation failed: {e}")
        flash("Error generating PDF.", "error")
        return redirect(url_for("dashboard.user_dashboard"))
    
    # Return the generated PDF as a response.
    return send_file(pdf_file, mimetype="application/pdf", as_attachment=False)


@dashboard.route("/dashboard/view_request/<int:request_id>")
@active_required
def view_request_details(request_id):
    """View details of a specific request for a student"""
    # Redirect to the approval view route
    return redirect(url_for("approval.view_request", request_id=request_id))

@dashboard.route("/affidavit_intent", methods=["GET", "POST"])
@active_required
def affidavit_intent():
    if request.method == "POST":
        # Get form data
        student_name = session.get("user", "Unknown")
        student_id = request.form["student_id"]
        date_of_birth = request.form["date_of_birth"]
        age = request.form.get("age")
        county = request.form.get("county")
        college = request.form.get("college", "University of Houston")
        signature_date = request.form.get("signature_date", datetime.now().strftime("%m-%d-%Y"))

        # Handle signature upload
        signature_base64 = None
        if 'signature' in request.files:
            signature_file = request.files['signature']
            if signature_file and signature_file.filename != '':
                # Read binary data
                binary_data = signature_file.read()
                # Convert binary data to base64 encoded string
                signature_base64 = base64.b64encode(binary_data).decode('utf-8')
                
                # Reset file pointer to beginning of file
                signature_file.seek(0)
                
                # Save file to 'app/static/uploads' folder
                from werkzeug.utils import secure_filename
                signature_filename = secure_filename(signature_file.filename)
                upload_folder = os.path.join("app", "static", "uploads")
                os.makedirs(upload_folder, exist_ok=True)
                upload_path = os.path.join(upload_folder, signature_filename)
                signature_file.save(upload_path)

        request_data = {
            "student_name": student_name,
            "student_id": student_id,
            "date_of_birth": date_of_birth,
            "age": age,
            "county": county,
            "college": college,
            "signature_date": signature_date,
            "signature": signature_base64
        }

        # Determine whether to save as draft or submit
        action = request.form.get("action")
        status = "draft" if action == "save_draft" else "under_review"

        academic_service.submit_form(request_data, 3, status)
        flash("Draft saved successfully." if status == "draft" else "Form submitted successfully.", "success")
        return redirect(url_for("dashboard.user_dashboard"))

    return render_template("affidavit_intent.html", current_date=datetime.now().strftime("%m-%d-%Y"))

@dashboard.route("/tuition_exemption", methods=["GET", "POST"])
@active_required
def tuition_exemption():
    if request.method == "POST":
        # Get form data
        student_name = session.get("user", "Unknown")
        student_id = request.form["student_id"]
        email = session.get("email", "Unknown")
        phone = request.form["phone"]
        semester = request.form["semester"]
        exemption_type = request.form["exemption_type"]
        department = request.form["department"]
        disclosure_type = request.form["disclosure_type"]
        recipient_type = request.form["recipient_type"]
        exemption_reason = request.form["exemption_reason"]
        
        # Get supporting documents
        supporting_documents = []
        if 'supporting_docs' in request.files:
            files = request.files.getlist('supporting_docs')
            for file in files:
                if file and file.filename != '':
                    from werkzeug.utils import secure_filename
                    doc_filename = secure_filename(f"doc_{uuid.uuid4().hex}{os.path.splitext(file.filename)[1]}")
                    upload_folder = os.path.join("app", "static", "uploads")
                    os.makedirs(upload_folder, exist_ok=True)
                    upload_path = os.path.join(upload_folder, doc_filename)
                    file.save(upload_path)
                    supporting_documents.append(doc_filename)
        
        # Handle signature upload
        signature_base64 = None
        if 'signature' in request.files:
            signature_file = request.files['signature']
            if signature_file and signature_file.filename != '':
                # Read binary data
                binary_data = signature_file.read()
                # Convert binary data to base64 encoded string
                signature_base64 = base64.b64encode(binary_data).decode('utf-8')
                
                # Reset file pointer to beginning of file
                signature_file.seek(0)
                
                # Save file to uploads folder
                from werkzeug.utils import secure_filename
                signature_filename = secure_filename(signature_file.filename)
                upload_folder = os.path.join("app", "static", "uploads")
                os.makedirs(upload_folder, exist_ok=True)
                upload_path = os.path.join(upload_folder, signature_filename)
                signature_file.save(upload_path)
        
        signature_date = request.form.get("signature_date", datetime.now().strftime("%m-%d-%Y"))

        request_data = {
            "student_name": student_name,
            "student_id": student_id,
            "email": email,
            "phone": phone,
            "semester": semester,
            "exemption_type": exemption_type,
            "department": department,
            "disclosure_type": disclosure_type,
            "recipient_type": recipient_type,
            "exemption_reason": exemption_reason,
            "supporting_documents": supporting_documents,
            "signature": signature_base64,
            "signature_date": signature_date
        }

        # Determine whether to save as draft or submit
        action = request.form.get("action")
        status = "draft" if action == "save_draft" else "under_review"

        academic_service.submit_form(request_data, 4, status)
        flash("Draft saved successfully." if status == "draft" else "Form submitted successfully.", "success")
        return redirect(url_for("dashboard.user_dashboard"))

    return render_template("tuition_exemption.html", current_date=datetime.now().strftime("%m-%d-%Y"))

@dashboard.route("/affidavit_intent/edit/<int:request_id>", methods=["GET", "POST"])
@active_required
def affidavit_intent_edit(request_id):
    draft = AcademicRequests.query.filter_by(id=request_id, email=session.get("email")).first_or_404()
    if request.method == "POST":
        # Get form data
        student_name = session.get("user", "Unknown")
        student_id = request.form["student_id"]
        date_of_birth = request.form["date_of_birth"]
        age = request.form.get("age")
        county = request.form.get("county")
        college = request.form.get("college", "University of Houston")
        signature_date = request.form.get("signature_date", datetime.now().strftime("%m-%d-%Y"))

        # Handle signature upload
        signature_file = request.files.get("signature")
        if signature_file and signature_file.filename != "":
            # Read binary data before saving the file
            binary_data = signature_file.read()
            # Convert binary data to base64 encoded string
            signature_base64 = base64.b64encode(binary_data).decode('utf-8')
            
            # Reset file pointer to beginning of file
            signature_file.seek(0)
            
            # Save file to 'app/static/uploads' folder
            from werkzeug.utils import secure_filename
            signature_filename = secure_filename(signature_file.filename)
            upload_folder = os.path.join("app", "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            upload_path = os.path.join(upload_folder, signature_filename)
            signature_file.save(upload_path)
            
            # Update signature in draft data
            draft.data["signature"] = signature_base64

        # Update other form fields
        draft.data["student_name"] = student_name
        draft.data["student_id"] = student_id
        draft.data["date_of_birth"] = date_of_birth
        draft.data["age"] = age
        draft.data["county"] = county
        draft.data["college"] = college
        draft.data["signature_date"] = signature_date

        db.session.commit()
        flash("Form updated successfully.", "success")
        return redirect(url_for("dashboard.user_dashboard"))

    return render_template("affidavit_intent.html", draft=draft.data, current_date=datetime.now().strftime("%m-%d-%Y"))

@dashboard.route("/tuition_exemption/edit/<int:request_id>", methods=["GET", "POST"])
@active_required
def tuition_exemption_edit(request_id):
    draft = AcademicRequests.query.filter_by(id=request_id, email=session.get("email")).first_or_404()
    if request.method == "POST":
        # Get form data
        student_name = session.get("user", "Unknown")
        student_id = request.form["student_id"]
        email = session.get("email", "Unknown")
        phone = request.form["phone"]
        semester = request.form["semester"]
        exemption_type = request.form["exemption_type"]
        department = request.form["department"]
        disclosure_type = request.form["disclosure_type"]
        recipient_type = request.form["recipient_type"]
        exemption_reason = request.form["exemption_reason"]
        signature_date = request.form.get("signature_date", datetime.now().strftime("%m-%d-%Y"))
        
        # Handle new supporting documents if uploaded
        if 'supporting_docs' in request.files:
            files = request.files.getlist('supporting_docs')
            supporting_documents = draft.data.get("supporting_documents", [])
            
            for file in files:
                if file and file.filename != "":
                    from werkzeug.utils import secure_filename
                    doc_filename = secure_filename(f"doc_{uuid.uuid4().hex}{os.path.splitext(file.filename)[1]}")
                    upload_folder = os.path.join("app", "static", "uploads")
                    os.makedirs(upload_folder, exist_ok=True)
                    upload_path = os.path.join(upload_folder, doc_filename)
                    file.save(upload_path)
                    supporting_documents.append(doc_filename)
            
            draft.data["supporting_documents"] = supporting_documents
        
        # Handle signature upload
        signature_file = request.files.get("signature")
        if signature_file and signature_file.filename != "":
            # Read binary data before saving the file
            binary_data = signature_file.read()
            # Convert binary data to base64 encoded string
            signature_base64 = base64.b64encode(binary_data).decode('utf-8')
            
            # Reset file pointer to beginning of file
            signature_file.seek(0)
            
            # Save file to uploads folder
            from werkzeug.utils import secure_filename
            signature_filename = secure_filename(signature_file.filename)
            upload_folder = os.path.join("app", "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            upload_path = os.path.join(upload_folder, signature_filename)
            signature_file.save(upload_path)
            
            # Update signature in draft data
            draft.data["signature"] = signature_base64

        # Update other form fields
        draft.data["student_name"] = student_name
        draft.data["student_id"] = student_id
        draft.data["email"] = email
        draft.data["phone"] = phone
        draft.data["semester"] = semester
        draft.data["exemption_type"] = exemption_type
        draft.data["department"] = department
        draft.data["disclosure_type"] = disclosure_type
        draft.data["recipient_type"] = recipient_type
        draft.data["exemption_reason"] = exemption_reason
        draft.data["signature_date"] = signature_date

        db.session.commit()
        flash("Form updated successfully.", "success")
        return redirect(url_for("dashboard.user_dashboard"))

    return render_template("tuition_exemption.html", draft=draft.data, current_date=datetime.now().strftime("%m-%d-%Y"))

