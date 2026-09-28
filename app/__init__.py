import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Vui long dang nhap de tiep tuc."


def create_app(config_override=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("app.config.Config")
    if config_override:
        app.config.update(config_override)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    from app.security import csrf_token
    app.jinja_env.globals["csrf_token"] = csrf_token

    from app import models  # noqa: F401  (dang ky models voi SQLAlchemy)

    # --- dang ky blueprints ---
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.member import member_bp
    from app.routes.event import event_bp
    from app.routes.funds import funds_bp
    from app.routes.ai import ai_bp
    from app.routes.admin import admin_bp
    from app.routes.profile import profile_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(funds_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    if not app.config.get("TESTING"):
        from app.scheduler import init_scheduler
        init_scheduler(app)

    return app
