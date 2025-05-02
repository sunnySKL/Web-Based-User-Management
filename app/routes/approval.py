from flask import Blueprint, render_template, request, session, redirect, url_for, flash, send_file
from fpdf import FPDF
import os
import json
from datetime import datetime
import app.services.approval_service as approval_service
import app.services.academic_service as academic_service
from app.models import User
from app.decorators import active_required
import base64
import shutil
import subprocess
from flask import current_app
from app.extensions.db import db

# Create a Flask Blueprint for the Approval System
approval_bp = Blueprint("approval", __name__, template_folder="../templates", static_folder="../static")

# Ensure directories exist
PDF_FOLDER = "app/static/pdfs/"
SIGNATURE_FOLDER = "app/static/signatures/"
COMMENTS_FOLDER = "app/static/comments/"
if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)
if not os.path.exists(SIGNATURE_FOLDER):
    os.makedirs(SIGNATURE_FOLDER)
if not os.path.exists(COMMENTS_FOLDER):
    os.makedirs(COMMENTS_FOLDER)

# File-based comment storage functions
def save_comment(request_id, approver_email, approver_role, status, comment):
    """Save a comment to a file for persistence across sessions"""
    comment_data = {
        "approver_email": approver_email,
        "approver_role": approver_role,
        "status": status,
        "comments": comment,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    comment_file = os.path.join(COMMENTS_FOLDER, f"comments_{request_id}.json")
    
    existing_comments = []
    # Read existing comments if file exists
    if os.path.exists(comment_file):
        try:
            with open(comment_file, 'r') as f:
                existing_comments = json.load(f)
                if not isinstance(existing_comments, list):
                    existing_comments = [existing_comments]
        except Exception as e:
            print(f"ERROR - Failed to read existing comments: {e}")
    
    # Add the new comment
    existing_comments.append(comment_data)
    
    # Write back all comments
    try:
        with open(comment_file, 'w') as f:
            json.dump(existing_comments, f)
        print(f"DEBUG - Saved comment to file: {comment_file}")
        return True
    except Exception as e:
        print(f"ERROR - Failed to save comment to file: {e}")
        return False

def get_comment(request_id):
    """Retrieve comments from the file system"""
    comment_file = os.path.join(COMMENTS_FOLDER, f"comments_{request_id}.json")
    
    if not os.path.exists(comment_file):
        # Try legacy filename format
        legacy_file = os.path.join(COMMENTS_FOLDER, f"comment_{request_id}.json")
        if os.path.exists(legacy_file):
            comment_file = legacy_file
        else:
            print(f"DEBUG - No comment file found for request {request_id}")
            return None
    
    try:
        with open(comment_file, 'r') as f:
            comments_data = json.load(f)
            if not isinstance(comments_data, list):
                comments_data = [comments_data]
        print(f"DEBUG - Loaded {len(comments_data)} comments from file")
        return comments_data
    except Exception as e:
        print(f"ERROR - Failed to load comments from file: {e}")
        return None

@approval_bp.route("/approvals/dashboard")
@active_required
def approval_dashboard():
    """Dashboard for approvers to see forms that need their approval"""
    user_role = session.get("role")
    
    # Check if user has an approver role
    if user_role not in [User.ROLE_DEPARTMENT_COUNSELOR, User.ROLE_ACADEMIC_DIRECTOR, User.ROLE_COLLEGE_SUPERVISOR]:
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("main.home"))
    
    # Get pending requests for the user's role
    pending_requests = approval_service.get_pending_requests(user_role)
    
    return render_template(
        "approval_dashboard.html", 
        pending_requests=pending_requests,
        user_role=user_role
    )

@approval_bp.route("/approvals/view/<int:request_id>")
@active_required
def view_request(request_id):
    """View details of a specific request"""
    user_role = session.get("role")
    user_email = session.get("email")
    
    try:
        # Get the request
        form_request = academic_service.get_form_by_id(request_id)
        
        # Check permissions: approvers can view any request, users can only view their own
        if user_role not in [User.ROLE_DEPARTMENT_COUNSELOR, User.ROLE_ACADEMIC_DIRECTOR, User.ROLE_COLLEGE_SUPERVISOR]:
            # Regular users can only view their own requests
            if form_request.email != user_email:
                flash("You do not have permission to access this request", "error")
                return redirect(url_for("dashboard.user_dashboard"))
        
        # Log debug information
        print(f"DEBUG - Request ID: {request_id}")
        print(f"DEBUG - User role: {user_role}")
        print(f"DEBUG - Request status: {form_request.status}")
        print(f"DEBUG - Current approver: {form_request.current_approver}")
        
        # Get comments from file system (persists across users)
        file_comment = get_comment(request_id)
        if file_comment:
            print(f"DEBUG - Found file comment: {file_comment}")
        
        return render_template(
            "view_request.html",
            request=form_request,
            file_comment=file_comment
        )
    except Exception as e:
        current_app.logger.error(f"Error viewing request: {e}")
        flash(f"An error occurred while viewing the request: {str(e)}", "error")
        if user_role in [User.ROLE_DEPARTMENT_COUNSELOR, User.ROLE_ACADEMIC_DIRECTOR, User.ROLE_COLLEGE_SUPERVISOR]:
            return redirect(url_for("approval.approval_dashboard"))
        else:
            return redirect(url_for("dashboard.user_dashboard"))

@approval_bp.route("/approvals/process/<int:request_id>", methods=["POST"])
@active_required
def process_approval(request_id):
    """Process an approval or rejection"""
    user_role = session.get("role")
    user_email = session.get("email")
    
    # Check if user has an approver role
    if user_role not in [User.ROLE_DEPARTMENT_COUNSELOR, User.ROLE_ACADEMIC_DIRECTOR, User.ROLE_COLLEGE_SUPERVISOR]:
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("main.home"))
    
    action = request.form.get("action")
    comments = request.form.get("comments")
    
    # Store the comment in file system if it exists (even if empty)
    save_comment(
        request_id, 
        user_email, 
        user_role,
        'skipped' if action == 'skip' else ('rejected' if action == 'reject' else 'approved'),
        comments or 'No comments provided'
    )
    
    try:
        if action == "approve":
            success, message = approval_service.approve_request(request_id, user_email, user_role, comments)
            if success:
                # Green success message for approvals
                flash(message, "success")
            else:
                flash(message, "error")
        elif action == "reject":
            success, message = approval_service.reject_request(request_id, user_email, user_role, comments)
            if success:
                # Red error message for rejections
                flash(message, "error")
            else:
                flash(message, "error")
        elif action == "skip":
            # Only Department Counselor and Academic Director can skip
            if user_role not in [User.ROLE_DEPARTMENT_COUNSELOR, User.ROLE_ACADEMIC_DIRECTOR]:
                flash("You are not authorized to skip this review", "error")
            else:
                success, message = approval_service.skip_review(request_id, user_email, user_role, comments)
                if success:
                    # Blue info message for skipped reviews
                    flash(message, "info")
                else:
                    flash(message, "error")
        else:
            flash("Invalid action", "error")
    except Exception as e:
        current_app.logger.error(f"Error processing approval/rejection: {e}")
        flash(f"An error occurred while processing the request: {str(e)}", "error")
    
    return redirect(url_for("approval.approval_dashboard"))

@approval_bp.route("/form_submit/thesis", methods=["GET", "POST"])
def form_submit_thesis():
    if request.method == "POST":
        first_name = session.get("first_name", "Unknown")
        middle_initial = session.get("middle_initial", "")
        last_name = session.get("last_name", "Unknown")
        uh_id = session.get("uh_id", "Unknown")
        student_email = session.get("student_email", "Unknown")
        degree = request.form["degree"]
        program = request.form["program"]
        defense_date = request.form["defense_date"]
        graduation_date = request.form["graduation_date"]
        thesis_title = request.form["thesis_title"]
        date = datetime.now().strftime("%Y-%m-%d")

        full_name = f"{first_name} {middle_initial} {last_name}".strip()

        # Handle signature upload
        signature_path = None
        if "signature" in request.files:
            signature = request.files["signature"]
            if signature.filename != "":
                signature_path = os.path.join(SIGNATURE_FOLDER, f"{uh_id}_signature.png")
                signature.save(signature_path)

        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, "Written Thesis Approval Form", ln=True, align="C")
        pdf.ln(10)
        pdf.cell(200, 10, f"Student Name: {full_name}", ln=True)
        pdf.cell(200, 10, f"UH ID: {uh_id}", ln=True)
        pdf.cell(200, 10, f"Student Email: {student_email}", ln=True)
        pdf.cell(200, 10, f"Degree: {degree}", ln=True)
        pdf.cell(200, 10, f"Program: {program}", ln=True)
        pdf.cell(200, 10, f"Defense Date: {defense_date}", ln=True)
        pdf.cell(200, 10, f"Anticipated Graduation Date: {graduation_date}", ln=True)
        pdf.cell(200, 10, f"Thesis Title: {thesis_title}", ln=True)
        pdf.cell(200, 10, f"Submission Date: {date}", ln=True)

        # Add signature if uploaded
        if signature_path:
            pdf.image(signature_path, x=10, y=pdf.get_y() + 10, w=40, h=20)

        # Save PDF
        pdf_path = os.path.join(PDF_FOLDER, f"{uh_id}_thesis_approval.pdf")
        pdf.output(pdf_path)

        return f"Form submitted! <a href='/{pdf_path}'>Download PDF</a>"

    return render_template("form_submit_thesis.html")

@approval_bp.route("/form_submit/drop", methods=["GET", "POST"])
def form_submit_drop():
    return render_template("form_submit_drop.html")

@approval_bp.route("/view_pdf/<int:request_id>", methods=["GET"])
@active_required
def view_pdf(request_id):
    """View PDF for a specific request"""
    user_role = session.get("role")
    user_email = session.get("email")
    
    try:
        # Get the request
        form_request = academic_service.get_form_by_id(request_id)
        
        # Check permissions: approvers can view any PDF, users can only view their own
        if user_role not in [User.ROLE_DEPARTMENT_COUNSELOR, User.ROLE_ACADEMIC_DIRECTOR, User.ROLE_COLLEGE_SUPERVISOR]:
            # Regular users can only view their own requests
            if form_request.email != user_email:
                flash("You do not have permission to access this PDF", "error")
                return redirect(url_for("dashboard.user_dashboard"))
        
        request_data = form_request.data.copy()
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
        if form_request.form_type == 1: 
            rendered_tex = render_template("special_circumstance.tex.j2", request_data=request_data)
            tex_file = os.path.join(temp_dir, "special_circumstance.tex")
            pdf_file = os.path.join(temp_dir, "special_circumstance.pdf")
        elif form_request.form_type == 2:
            rendered_tex = render_template("course_drop.tex.j2", request_data=request_data)
            tex_file = os.path.join(temp_dir, "course_drop.tex")
            pdf_file = os.path.join(temp_dir, "course_drop.pdf")
        elif form_request.form_type == 3:
            rendered_tex = render_template("affidavit_intent.tex.j2", request_data=request_data)
            tex_file = os.path.join(temp_dir, "affidavit_intent.tex")
            pdf_file = os.path.join(temp_dir, "affidavit_intent.pdf")
        elif form_request.form_type == 4:
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
            
            if form_request.form_type == 2:
                print("Compiling course_drop.pdf")
                result = subprocess.run(["make", "-C", temp_dir, "course_drop.pdf"], check=True, capture_output=True, text=True)
                print(f"Compilation output: {result.stdout}")
                if result.stderr:
                    print(f"Compilation errors: {result.stderr}")
                    
                # Run twice for references
                subprocess.run(["make", "-C", temp_dir, "course_drop.pdf"], check=True)
            elif form_request.form_type == 3:
                print("Compiling affidavit_intent.pdf")
                result = subprocess.run(["make", "-C", temp_dir, "affidavit_intent.pdf"], check=True, capture_output=True, text=True)
                print(f"Compilation output: {result.stdout}")
                if result.stderr:
                    print(f"Compilation errors: {result.stderr}")
                    
                # Run twice for references
                subprocess.run(["make", "-C", temp_dir, "affidavit_intent.pdf"], check=True)
            elif form_request.form_type == 4:
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
            return redirect(url_for("dashboard.user_dashboard") if user_role == User.ROLE_USER else url_for("approval.approval_dashboard"))
        
        # Return the generated PDF as a response.
        return send_file(pdf_file, mimetype="application/pdf", as_attachment=False)
    except Exception as e:
        current_app.logger.error(f"Error generating PDF: {e}")
        flash(f"Error generating PDF: {str(e)}", "error")
        return redirect(url_for("dashboard.user_dashboard") if user_role == User.ROLE_USER else url_for("approval.approval_dashboard"))
