import os
from flask import Flask

def create_app():
    app = Flask(__name__, template_folder=os.path.abspath("app/templates"),
               static_folder=os.path.abspath("app/static"))

    # Set a secret key for session management
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')

    # Import and register Blueprints
    from app.routes.main import main
    from app.routes.auth import auth
    from app.routes.admin import admin
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(admin)

    return app
