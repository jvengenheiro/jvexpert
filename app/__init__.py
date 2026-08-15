from pathlib import Path

from flask import Flask

from app.models import db

INSTANCE_DIR = Path(__file__).resolve().parent.parent / "instance"


def create_app():
    INSTANCE_DIR.mkdir(exist_ok=True)

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{INSTANCE_DIR / 'escala.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev"
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB, planilhas de import

    db.init_app(app)

    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.instrutores import bp as instrutores_bp
    from app.routes.cursos import bp as cursos_bp
    from app.routes.importar import bp as importar_bp
    from app.routes.escala import bp as escala_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(instrutores_bp)
    app.register_blueprint(cursos_bp)
    app.register_blueprint(importar_bp)
    app.register_blueprint(escala_bp)

    with app.app_context():
        db.create_all()

    return app
