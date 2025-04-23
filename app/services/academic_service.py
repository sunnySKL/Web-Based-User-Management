from flask import session, request
import os
from app.models import AcademicRequests, User
from app.extensions.db import db
from werkzeug.utils import secure_filename
import app.services.workflow_service as workflow_service


API_BASE_URL = 'http://localhost:8000/admin/api/forms/'


def get_all_forms():
    pass

#form_type = 1 -> special circumstance
def submit_form(data, form_type, status):
    # Only determine workflow when actually submitting (not for drafts)
    current_approver = None
    if status == "under_review":
        # Get default workflow and determine first approver
        workflow = workflow_service.get_default_workflow()
        if workflow:
            steps = workflow_service.get_workflow_steps(workflow.id)
            if steps and len(steps) > 0:
                # Get the first step in the workflow
                first_step = steps[0]
                # Map UI role to internal role identifier
                role_mapping = {
                    User.ROLE_DEPARTMENT_COUNSELOR: "department_counselor",
                    User.ROLE_ACADEMIC_DIRECTOR: "academic_director", 
                    User.ROLE_COLLEGE_SUPERVISOR: "college_supervisor"
                }
                current_approver = role_mapping.get(first_step.role, "department_counselor")
            else:
                # Fallback to default if no steps found
                current_approver = "department_counselor"
        else:
            # Fallback to default if no workflow found
            current_approver = "department_counselor"
    
    new_request = AcademicRequests(
        email=session.get("email"),
        form_type=form_type,  
        data=data,
        status=status,
        current_approver=current_approver
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
        
        # Get default workflow and determine first approver
        workflow = workflow_service.get_default_workflow()
        if workflow:
            steps = workflow_service.get_workflow_steps(workflow.id)
            if steps and len(steps) > 0:
                # Get the first step in the workflow
                first_step = steps[0]
                # Map UI role to internal role identifier
                role_mapping = {
                    User.ROLE_DEPARTMENT_COUNSELOR: "department_counselor",
                    User.ROLE_ACADEMIC_DIRECTOR: "academic_director", 
                    User.ROLE_COLLEGE_SUPERVISOR: "college_supervisor"
                }
                draft.current_approver = role_mapping.get(first_step.role, "department_counselor")
            else:
                # Fallback to default if no steps found
                draft.current_approver = "department_counselor"
        else:
            # Fallback to default if no workflow found
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
