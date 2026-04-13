import os
import sys

from flask import Flask, jsonify, request
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
import urllib.request
import json
...
app.register_blueprint(activity_logs_bp)

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
    app.run(debug=True, port=5000)
