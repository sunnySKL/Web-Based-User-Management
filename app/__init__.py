from flask import Flask

#TODO: add config files to read from so we can have prod, test, dry-run features.
def create_app(config_class = "config.config"):
    app = Flask(__name__, instance_relative_config = True)

    #loading default config
    app.config.from_object(config_class)

    #register blueprints
    from .routes.main import main_blueprint as mbp

    app.register_blueprint(mbp)

    return app
