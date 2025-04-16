from datetime import datetime, timezone, timedelta
from .extensions.db import db
#from flask_login import UserMixin

class User(db.Model):
    __tablename__ = "users"

    # Role constants
    ROLE_USER = "User"
    ROLE_ADMIN = "Admin"
    ROLE_DEPARTMENT_COUNSELOR = "Department Counselor"
    ROLE_ACADEMIC_DIRECTOR = "Academic Director"
    ROLE_COLLEGE_SUPERVISOR = "College Supervisor"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    status = db.Column(db.String(50), default="active")

    def __repr__(self):
        return f"<User {self.email}>"

class AcademicRequests(db.Model):
    __tablename__ = "academic_requests"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), nullable=False)
    form_type = db.Column(db.Integer, nullable=False)  # e.g., "Transcript Request", etc.
    data = db.Column(db.JSON, nullable=False)             # JSON/text containing form data
    status = db.Column(db.String(20), default="draft")    # draft, pending, returned, approved, rejected, etc.
    current_approver = db.Column(db.String(50), default="department_counselor")  # department_counselor, academic_director, college_supervisor
    created_at = db.Column(db.DateTime, default = lambda: datetime.now(timezone(-timedelta(hours=5)).utc))
    
    # Use cascade="all" instead of "all, delete-orphan" to prevent deletion issues
    # and add passive_deletes=True to allow deletion of requests even if approval_logs table doesn't exist
    approval_logs = db.relationship('ApprovalLog', backref='request', lazy=True, 
                                  cascade="all", passive_deletes=True)

    def __repr__(self):
        return f"<AcademicRequest {self.id} for {self.email}>"
        
class ApprovalLog(db.Model):
    __tablename__ = "approval_logs"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_id = db.Column(db.Integer, db.ForeignKey('academic_requests.id'), nullable=False)
    approver_email = db.Column(db.String(100), nullable=False)
    approver_role = db.Column(db.String(50), nullable=False)  # department_counselor, academic_director, college_supervisor
    status = db.Column(db.String(20), nullable=False)  # approved, rejected
    comments = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone(-timedelta(hours=5)).utc))
    
    def __repr__(self):
        return f"<ApprovalLog {self.id} for request {self.request_id} by {self.approver_role}>"
