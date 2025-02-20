from .extensions.db import db
#from flask_login import UserMixin

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), default='User')

    def __repr__(self):
        return f"<User {self.email}>"
