from pathlib import Path
import os

from flask import Flask, g, session
from flask_cors import CORS
from dotenv import load_dotenv

from app.persistence import close_db, get_user_by_id, init_db
from app.routes.web import web_bp


def create_app(test_config: dict | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    default_sqlite_path = Path(app.instance_path) / "bnf_validator.sqlite3"
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-bnf-validator-secret"),
        DATABASE_URL=normalize_database_url(
            os.environ.get("DATABASE_URL", f"sqlite:///{default_sqlite_path.as_posix()}")
        ),
        SESSION_COOKIE_SAMESITE=os.environ.get("SESSION_COOKIE_SAMESITE", "None"),
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "True").lower() in ("1", "true", "yes"),
    )
    if test_config:
        if "DATABASE_URL" in test_config:
            test_config = {
                **test_config,
                "DATABASE_URL": normalize_database_url(test_config["DATABASE_URL"]),
            }
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_db(app)
    CORS(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": os.environ.get("CORS_ALLOWED_ORIGINS", "*")}},
    )

    @app.before_request
    def load_current_user():
        user_id = session.get("user_id")
        g.user = None if user_id is None else get_user_by_id(app, user_id)

    @app.teardown_appcontext
    def teardown_db(_exception):
        close_db()

    app.register_blueprint(web_bp)
    return app


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


# Export an application instance so "gunicorn app:app" works when
# the platform invokes the package directly.
app = create_app()
