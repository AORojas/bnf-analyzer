from pathlib import Path

from flask import Flask, g, session

from app.persistence import close_db, get_user_by_id, init_db
from app.routes.web import web_bp


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY="dev-bnf-validator-secret",
        DATABASE=str(Path(app.instance_path) / "bnf_validator.sqlite3"),
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_db(app)

    @app.before_request
    def load_current_user():
        user_id = session.get("user_id")
        g.user = None if user_id is None else get_user_by_id(app, user_id)

    @app.teardown_appcontext
    def teardown_db(_exception):
        close_db()

    app.register_blueprint(web_bp)
    return app
