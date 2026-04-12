import os
import sys

from flask import Flask, jsonify
from flask_cors import CORS

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.core.database import Base, engine, ensure_sqlite_compatibility
from backend.app.routers import auth_bp, expenses_bp, groups_bp, settlements_bp, activity_logs_bp
import backend.app.models  # noqa: F401

app = Flask(__name__)

# Allow any origin for local development.
# Keep credentials disabled so wildcard CORS remains valid.
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.register_blueprint(auth_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(groups_bp)
app.register_blueprint(settlements_bp)
app.register_blueprint(activity_logs_bp)

Base.metadata.create_all(bind=engine)
ensure_sqlite_compatibility()



if __name__ == '__main__':
    app.run(debug=True, port=5000)
