import os
import sys
import urllib.request
import json
import logging
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from flask_cors import CORS

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.core.database import Base, engine, ensure_sqlite_compatibility
from backend.app.routers import auth_bp, expenses_bp, groups_bp, settlements_bp, activity_logs_bp
from backend.app.core.logging_config import setup_logging
import backend.app.models  # noqa: F401

app = Flask(__name__)
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend" / "src"

# Initialize Security Logging
security_logger = setup_logging(app)
security_logger.info("SYSTEM_STARTUP | Success | UniSplit Backend is starting up")

# Allow any origin for local development.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(groups_bp)
app.register_blueprint(settlements_bp)
app.register_blueprint(activity_logs_bp)


@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def serve_frontend_file(filename: str):
    if filename.startswith("api/"):
        abort(404)

    candidate = FRONTEND_DIR / filename
    if candidate.is_file():
        return send_from_directory(FRONTEND_DIR, filename)

    abort(404)

@app.route('/api/currencies')
def get_currencies():
    base = request.args.get('from', 'USD')
    try:
        url = f"https://api.frankfurter.app/latest?from={base}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return jsonify(data)
    except Exception as e:
        print(f"DEBUG: Currency API Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

Base.metadata.create_all(bind=engine)
ensure_sqlite_compatibility()

if __name__ == '__main__':
    app.run(debug=True, host="127.0.0.1", port=5000)
