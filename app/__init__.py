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
    from app.hardening import configure_security
    configure_security(app)

    db.init_app(app)
    login_manager.init_app(app)
    from app.security import csrf_token
    app.jinja_env.globals["csrf_token"] = csrf_token
    from app.services.ui_context import workspace_context
    app.context_processor(workspace_context)

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

    from app.hardening import install_hardening
    install_hardening(app)
    from app.security import install_csrf
    install_csrf(app)

    with app.app_context():
        if db.engine.url.get_backend_name() == "sqlite":
            from app.migrations import migrate_chat_conversations

            database_path = db.engine.url.database or ":memory:"
            backup = migrate_chat_conversations(database_path)
            if backup:
                app.logger.info("AI chat migration backup created: %s", backup)
        db.create_all()

    if not app.config.get("TESTING") and app.config.get("SCHEDULER_ENABLED", True):
        from app.scheduler import init_scheduler
        init_scheduler(app)

    return app
