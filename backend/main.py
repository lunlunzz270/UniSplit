import os
import sys

from flask import Flask, jsonify
from flask_cors import CORS

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.core.database import Base, engine, ensure_sqlite_compatibility
from backend.app.routers import auth_bp, expenses_bp
import backend.app.models  # noqa: F401

app = Flask(__name__)

# Allow any origin for local development.
# Keep credentials disabled so wildcard CORS remains valid.
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.register_blueprint(auth_bp)
app.register_blueprint(expenses_bp)

Base.metadata.create_all(bind=engine)
ensure_sqlite_compatibility()

@app.route('/api/dashboard')
def get_dashboard_data():
    data = {
        "total_balance": 48.50,
        "groups": ["Trip to NYC", "Roommates"],
        "recent_activity": [
            {"desc": "Alice added Dinner", "amount": 60},
            {"desc": "You paid Rent", "amount": 500}
        ]
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
