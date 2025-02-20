# app/services/user_service.py
from app.models import User
from app.extensions.db import db

def get_all_users():
    return User.query.all()

def create_user(display_name, email, role="User", status="active"):
    user = User(display_name=display_name, email=email, role=role, status=status)
    db.session.add(user)
    db.session.commit()
    return user

def update_user(user, data):
    user.display_name = data.get("display_name", user.display_name)
    user.email = data.get("email", user.email)
    user.role = data.get("role", user.role)
    user.status = data.get("status", user.status)
    db.session.commit()
    return user

def delete_user(user):
    db.session.delete(user)
    db.session.commit()

