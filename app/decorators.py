from functools import wraps
from flask import session, abort

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "Admin":
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function
