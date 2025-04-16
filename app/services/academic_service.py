from flask import session, request
import os
from app.models import AcademicRequests
from app.extensions.db import db
from werkzeug.utils import secure_filename

def get_all_forms():
    pass

#form_type = 1 -> special circumstance
def submit_form(data, form_type, status):
    new_request = AcademicRequests(
        email=session.get("email"),
        form_type=form_type,  
        data=data,
        status=status,
        # When submitting a form, set the first approver in the sequence
        current_approver="department_counselor" if status == "under_review" else None
    )
    db.session.add(new_request)
    db.session.commit()
    return new_request.id


def update_form(id, form_type, updated_data):
    draft = AcademicRequests.query.filter_by(id=id, email=session.get("email")).first_or_404()
    
    # Update the data field with the updated_data
    draft.data = updated_data
    
    # If the form is being submitted (not just saved as draft)
    if updated_data.get("action") != "save_draft":
        draft.status = "under_review"
        draft.current_approver = "department_counselor"
    
    db.session.commit()

def delete_form(id):
    draft = AcademicRequests.query.filter_by(id=id, email=session.get("email")).first_or_404()
    
    # Delete the draft and commit changes
    db.session.delete(draft)
    db.session.commit()

def get_user_forms(email):
    """Get all forms submitted by a user"""
    return AcademicRequests.query.filter_by(email=email).all()

def get_form_by_id(form_id):
    """Get a specific form by ID"""
    return AcademicRequests.query.get_or_404(form_id)


