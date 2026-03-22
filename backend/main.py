from flask import Flask, jsonify
from flask_cors import CORS
from app.core import init_db, db
from app.routers import auth_bp

app = Flask(__name__)
CORS(app)

init_db(app)

app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()

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