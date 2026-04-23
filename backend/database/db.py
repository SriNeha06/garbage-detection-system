from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_app(app):
    """Initialize the database with the Flask application."""
    db.init_app(app)
    with app.app_context():
        # Import models so they are registered with SQLAlchemy
        from . import models  # noqa: F401
        db.create_all()
