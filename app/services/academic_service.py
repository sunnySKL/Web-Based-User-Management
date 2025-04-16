from flask import session, request
import os
from app.models import AcademicRequests
from app.extensions.db import db
from werkzeug.utils import secure_filename


API_BASE_URL = 'http://localhost:8000/admin/api/forms/'


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


def api_create_form(data):
    response = requests.post(API_BASE_URL, json=data)
    return response.json()


def api_get_form(form_id):
    """
    Retrieves form details by performing a GET request for the given form_id.
    """
    url = f"{API_BASE_URL}{form_id}/"
    response = requests.get(url)
    return response.json()

def api_update_form(form_id, data):
    """
    Updates a form by sending a POST to the edit endpoint.
    `data` should be a JSON dictionary containing updated field values.
    """
    url = f"{API_BASE_URL}{form_id}/edit/"
    response = requests.post(url, json=data)
    return response.json()

def api_delete_form(form_id):
    """
    Deletes a form by sending a POST to the delete endpoint.
    """
    url = f"{API_BASE_URL}{form_id}/delete/"
    response = requests.post(url)
    return response.json()
