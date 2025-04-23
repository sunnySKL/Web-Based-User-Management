from app.models import ApprovalWorkflow, WorkflowStep, User
from app.extensions.db import db
from flask import current_app
import json

def get_all_workflows():
    """Get all workflow configurations"""
    return ApprovalWorkflow.query.all()

def get_workflow_by_id(workflow_id):
    """Get a specific workflow by ID"""
    return ApprovalWorkflow.query.get_or_404(workflow_id)

def get_default_workflow():
    """Get the default workflow"""
    return ApprovalWorkflow.query.filter_by(name="Default Approval Workflow").first()

def get_workflow_steps(workflow_id):
    """Get all steps for a specific workflow"""
    return WorkflowStep.query.filter_by(workflow_id=workflow_id).order_by(WorkflowStep.step_order).all()

def create_workflow(name, description=None):
    """Create a new workflow"""
    workflow = ApprovalWorkflow(
        name=name,
        description=description
    )
    db.session.add(workflow)
    db.session.commit()
    return workflow.id

def update_workflow(workflow_id, name=None, description=None, is_active=None):
    """Update workflow details"""
    workflow = get_workflow_by_id(workflow_id)
    
    if name:
        workflow.name = name
    if description is not None:
        workflow.description = description
    if is_active is not None:
        workflow.is_active = is_active
    
    db.session.commit()
    return workflow

def delete_workflow(workflow_id):
    """Delete a workflow and all its steps"""
    workflow = get_workflow_by_id(workflow_id)
    
    # Don't allow deleting the default workflow
    if workflow.name == "Default Approval Workflow":
        return False, "Cannot delete the default workflow"
    
    db.session.delete(workflow)
    db.session.commit()
    return True, "Workflow deleted successfully"

def add_workflow_step(workflow_id, role, step_order, can_skip=False, is_required=True):
    """Add a step to a workflow"""
    # Validate role
    if role not in [User.ROLE_DEPARTMENT_COUNSELOR, User.ROLE_ACADEMIC_DIRECTOR, User.ROLE_COLLEGE_SUPERVISOR]:
        return False, f"Invalid role: {role}"
    
    # Check if step_order already exists
    existing_step = WorkflowStep.query.filter_by(workflow_id=workflow_id, step_order=step_order).first()
    if existing_step:
        # Shift all steps with equal or higher order up by one
        steps_to_shift = WorkflowStep.query.filter(
            WorkflowStep.workflow_id == workflow_id,
            WorkflowStep.step_order >= step_order
        ).all()
        
        for step in steps_to_shift:
            step.step_order += 1
    
    # Create the new step
    step = WorkflowStep(
        workflow_id=workflow_id,
        role=role,
        step_order=step_order,
        can_skip=can_skip,
        is_required=is_required
    )
    
    db.session.add(step)
    db.session.commit()
    return True, "Step added successfully"

def update_workflow_step(step_id, role=None, step_order=None, can_skip=None, is_required=None):
    """Update a workflow step"""
    step = WorkflowStep.query.get_or_404(step_id)
    
    if role:
        # Validate role
        if role not in [User.ROLE_DEPARTMENT_COUNSELOR, User.ROLE_ACADEMIC_DIRECTOR, User.ROLE_COLLEGE_SUPERVISOR]:
            return False, f"Invalid role: {role}"
        step.role = role
    
    if step_order is not None and step_order != step.step_order:
        # Handle reordering
        if step_order < step.step_order:
            # Moving earlier in sequence - shift other steps down
            steps_to_shift = WorkflowStep.query.filter(
                WorkflowStep.workflow_id == step.workflow_id,
                WorkflowStep.step_order >= step_order,
                WorkflowStep.step_order < step.step_order
            ).all()
            
            for s in steps_to_shift:
                s.step_order += 1
        else:
            # Moving later in sequence - shift other steps up
            steps_to_shift = WorkflowStep.query.filter(
                WorkflowStep.workflow_id == step.workflow_id,
                WorkflowStep.step_order <= step_order,
                WorkflowStep.step_order > step.step_order
            ).all()
            
            for s in steps_to_shift:
                s.step_order -= 1
        
        step.step_order = step_order
    
    if can_skip is not None:
        step.can_skip = can_skip
    
    if is_required is not None:
        step.is_required = is_required
    
    db.session.commit()
    return True, "Step updated successfully"

def delete_workflow_step(step_id):
    """Delete a workflow step and reorder remaining steps"""
    step = WorkflowStep.query.get_or_404(step_id)
    workflow_id = step.workflow_id
    step_order = step.step_order
    
    # Delete the step
    db.session.delete(step)
    
    # Reorder remaining steps
    steps_to_shift = WorkflowStep.query.filter(
        WorkflowStep.workflow_id == workflow_id,
        WorkflowStep.step_order > step_order
    ).all()
    
    for s in steps_to_shift:
        s.step_order -= 1
    
    db.session.commit()
    return True, "Step deleted successfully"

def get_next_approver_role(current_role, workflow_id=None):
    """
    Get the next approver in the workflow sequence
    This replaces the hardcoded APPROVAL_SEQUENCE in approval_service.py
    """
    if not workflow_id:
        workflow = get_default_workflow()
        if not workflow:
            # Fallback to hardcoded sequence if no workflow found
            hardcoded_sequence = ["Department Counselor", "Academic Director", "College Supervisor"]
            try:
                current_index = hardcoded_sequence.index(current_role)
                if current_index < len(hardcoded_sequence) - 1:
                    return hardcoded_sequence[current_index + 1]
                return None
            except ValueError:
                return None
        workflow_id = workflow.id
    
    # Get all steps for this workflow
    steps = get_workflow_steps(workflow_id)
    
    # Find the current step
    current_step = None
    for i, step in enumerate(steps):
        if step.role == current_role:
            current_step = i
            break
    
    # If current step not found or it's the last step, return None
    if current_step is None or current_step >= len(steps) - 1:
        return None
    
    # Return the next step's role
    return steps[current_step + 1].role 