from flask import session
from app.models import AcademicRequests, ApprovalLog, User
from app.extensions.db import db
from datetime import datetime

# Approval hierarchy constants
APPROVAL_SEQUENCE = [
    "department_counselor",
    "academic_director",
    "college_supervisor"
]

# Status constants
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved" 
STATUS_REJECTED = "rejected"
STATUS_UNDER_REVIEW = "under_review"

def get_pending_requests(approver_role):
    """Get all requests pending approval for a specific approver role"""
    role_mapping = {
        User.ROLE_DEPARTMENT_COUNSELOR: "department_counselor",
        User.ROLE_ACADEMIC_DIRECTOR: "academic_director", 
        User.ROLE_COLLEGE_SUPERVISOR: "college_supervisor"
    }
    
    if approver_role not in role_mapping:
        return []
    
    approver_stage = role_mapping[approver_role]
    
    # Get requests where current_approver matches the approver_stage and status is under_review
    # Sort by ID in descending order
    return AcademicRequests.query.filter_by(
        current_approver=approver_stage,
        status=STATUS_UNDER_REVIEW
    ).order_by(AcademicRequests.id.desc()).all()

def approve_request(request_id, approver_email, approver_role, comments=None):
    """Approve a request and move it to the next approval stage"""
    request = AcademicRequests.query.get_or_404(request_id)
    
    # Map UI role to internal role identifier
    role_mapping = {
        User.ROLE_DEPARTMENT_COUNSELOR: "department_counselor",
        User.ROLE_ACADEMIC_DIRECTOR: "academic_director", 
        User.ROLE_COLLEGE_SUPERVISOR: "college_supervisor"
    }
    
    approver_stage = role_mapping.get(approver_role)
    
    # Validate approver can approve this request
    if request.current_approver != approver_stage or request.status != STATUS_UNDER_REVIEW:
        return False, "You are not authorized to approve this request or it's not in the correct status."
    
    try:
        # Create approval log
        approval_log = ApprovalLog(
            request_id=request_id,
            approver_email=approver_email,
            approver_role=approver_role,
            status=STATUS_APPROVED,
            comments=comments
        )
        db.session.add(approval_log)
        
        # Get current position in approval sequence
        current_index = APPROVAL_SEQUENCE.index(approver_stage)
        
        # If this is the last approver in the sequence
        if current_index == len(APPROVAL_SEQUENCE) - 1:
            request.status = STATUS_APPROVED
        else:
            # Move to next approver in sequence
            request.current_approver = APPROVAL_SEQUENCE[current_index + 1]
        
        db.session.commit()
        return True, "Request approved successfully"
    except Exception as e:
        db.session.rollback()
        print(f"Error approving request: {e}")
        
        # Even if we can't create an approval log, still update the request status
        try:
            # Get current position in approval sequence
            current_index = APPROVAL_SEQUENCE.index(approver_stage)
            
            # If this is the last approver in the sequence
            if current_index == len(APPROVAL_SEQUENCE) - 1:
                request.status = STATUS_APPROVED
            else:
                # Move to next approver in sequence
                request.current_approver = APPROVAL_SEQUENCE[current_index + 1]
            
            db.session.commit()
            return True, "Request approved successfully"
        except Exception as inner_e:
            db.session.rollback()
            print(f"Error updating request status: {inner_e}")
            return False, f"Error processing approval: {str(e)}"

def reject_request(request_id, approver_email, approver_role, comments=None):
    """Reject a request"""
    request = AcademicRequests.query.get_or_404(request_id)
    
    # Map UI role to internal role identifier
    role_mapping = {
        User.ROLE_DEPARTMENT_COUNSELOR: "department_counselor",
        User.ROLE_ACADEMIC_DIRECTOR: "academic_director", 
        User.ROLE_COLLEGE_SUPERVISOR: "college_supervisor"
    }
    
    approver_stage = role_mapping.get(approver_role)
    
    # Validate approver can reject this request
    if request.current_approver != approver_stage or request.status != STATUS_UNDER_REVIEW:
        return False, "You are not authorized to reject this request or it's not in the correct status."
    
    try:
        # Store decision comments directly in the request data
        if comments and comments.strip():
            # Get the current data and add the decision information
            data = request.data.copy() if request.data else {}
            
            # Add or append to decision_comments in the data dictionary
            if "decision_comments" not in data:
                data["decision_comments"] = []
            
            # Add this decision to the comments history
            decision_record = {
                "approver_email": approver_email,
                "approver_role": approver_role,
                "status": STATUS_REJECTED,
                "comments": comments,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            data["decision_comments"].append(decision_record)
            
            # Debug print to verify data structure
            print(f"DEBUG - Updated data: {data}")
            print(f"DEBUG - Decision comments: {data.get('decision_comments')}")
            
            # Update the request data
            request.data = data
        
        # Try to create rejection log, but continue even if it fails
        try:
            rejection_log = ApprovalLog(
                request_id=request_id,
                approver_email=approver_email,
                approver_role=approver_role,
                status=STATUS_REJECTED,
                comments=comments
            )
            db.session.add(rejection_log)
        except Exception as log_error:
            print(f"Error creating rejection log: {log_error}")
            # Continue with the rejection process even if logging fails
        
        # Update request status
        request.status = STATUS_REJECTED
        
        # Ensure changes are committed to the database
        db.session.commit()
        
        # Verify the data was saved correctly
        updated_request = AcademicRequests.query.get(request_id)
        print(f"DEBUG - After commit data: {updated_request.data}")
        print(f"DEBUG - After commit decision_comments: {updated_request.data.get('decision_comments')}")
        
        return True, "Request rejected"
    except Exception as e:
        db.session.rollback()
        print(f"Error rejecting request: {e}")
        
        # Even if we can't create a rejection log, still update the request status
        try:
            request.status = STATUS_REJECTED
            db.session.commit()
            return True, "Request rejected"
        except Exception as inner_e:
            db.session.rollback()
            print(f"Error updating request status: {inner_e}")
            return False, f"Error processing rejection: {str(e)}"

def get_approval_history(request_id):
    """Get the approval history for a request"""
    try:
        return ApprovalLog.query.filter_by(request_id=request_id).order_by(ApprovalLog.timestamp.asc()).all()
    except Exception as e:
        # Handle case where approval_logs table might not exist
        print(f"Error retrieving approval history: {e}")
        return [] 