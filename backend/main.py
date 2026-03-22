from flask import Flask, jsonify

app = Flask(__name__)

# The frontend no longer requests the page, but requests data
@app.route('/api/dashboard')
def get_dashboard_data():
    # This will connect to a database in the future; for now, we'll use fake data instead.
    data = {
        "total_balance": 48.50,
        "groups": ["Trip to NYC", "Roommates"],
        "recent_activity": [
            {"desc": "Alice added Dinner", "amount": 60},
            {"desc": "You paid Rent", "amount": 500}
        ]
    }
    return jsonify(data) # 返回 JSON 给前端

if __name__ == '__main__':
    app.run(debug=True, port=5000)