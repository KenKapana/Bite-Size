from flask import Flask
import firebase_admin
from firebase_admin import credentials

from app.config import FLASK_SECRET, FIREBASE_DATABASE_URL

def create_app():
    """Initialize the Flask application."""
    app = Flask(
        __name__,
        static_folder='../static',         # path to static (relative to this file)
        template_folder='templates'        # still inside app/
    )
    
    app.secret_key = FLASK_SECRET
    
    # Initialize Firebase
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
    except ValueError:
        # Initialize Firebase if not already done
        firebase_cred = credentials.Certificate('firebase_credentials.json')
        firebase_admin.initialize_app(firebase_cred, {
            'databaseURL': FIREBASE_DATABASE_URL
        })
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.calendar import calendar_bp
    from app.routes.todo import todo_bp
    from app.routes.test import test_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(todo_bp)
    app.register_blueprint(test_bp)
    
    return app