import os
import sys
import urllib.request
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from flask_cors import CORS

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.core.database import Base, engine, ensure_sqlite_compatibility
from backend.app.routers import auth_bp, expenses_bp, groups_bp, settlements_bp, activity_logs_bp, reminders_bp, admin_bp
from backend.app.core.logging_config import setup_logging
import backend.app.models  # noqa: F401

app = Flask(__name__)
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend" / "src"

# Initialize database unless running in a test environment (where tests handle their own setup)
if "PYTEST_CURRENT_TEST" not in os.environ:
    try:
        Base.metadata.create_all(bind=engine)
        ensure_sqlite_compatibility()
    except Exception as e:
        print(f"DATABASE_INIT_FAIL | Error: {str(e)}")
        # Don't re-raise yet, let the app try to start so we see it in logs

# Initialize Security Logging
security_logger = setup_logging(app)
security_logger.info("SYSTEM_STARTUP | Success | UniSplit Backend is starting up")

def automated_reminder_worker():
    """Background task to send automatic reminders for unsettled expenses every 24 hours."""
    from backend.app.models.expenses import Expense, ExpenseParticipant
    from backend.app.repositories.reminders import ReminderRepository
    from backend.app.core.database import SessionLocal
    from sqlalchemy import func

    # Wait for system to settle
    time.sleep(10)
    
    while True:
        try:
            db = SessionLocal()
            now = datetime.now()
            # Find participants who haven't settled and need a reminder (24h since creation or last reminder)
            participants = (
                db.query(ExpenseParticipant)
                .join(Expense, ExpenseParticipant.expense_id == Expense.id)
                .filter(ExpenseParticipant.is_settled == False)
                .all()
            )
            
            reminder_repo = ReminderRepository(db)
            count = 0
            
            for p in participants:
                expense = p.expense
                # Check if we should remind: either never reminded or 24h passed
                last_time = p.last_reminder_at or expense.created_at
                if (now - last_time) >= timedelta(hours=24):
                    try:
                        msg = f"Automatic Reminder: You have an unsettled bill '{expense.description}' for ${float(p.share)}."
                        reminder_repo.create_reminder(
                            group_id=expense.group_id,
                            sender_id=expense.paid_by, # Send on behalf of the payer
                            recipient_id=p.user_id,
                            message=msg,
                            expense_id=expense.id
                        )
                        p.last_reminder_at = func.now()
                        p.reminder_count = (p.reminder_count or 0) + 1
                        count += 1
                    except Exception as e:
                        print(f"AUTO_REMINDER_ERR | Failed for user {p.user_id} on expense {expense.id}: {str(e)}")
            
            if count > 0:
                print(f"AUTO_REMINDER_SUCCESS | Sent {count} automatic reminders")
            
            db.commit()
            db.close()
        except Exception as e:
            print(f"AUTO_REMINDER_WORKER_ERR | {str(e)}")
        
        # Check every hour
        time.sleep(3600)

# Start background worker
reminder_thread = threading.Thread(target=automated_reminder_worker, daemon=True)
reminder_thread.start()

# Allow any origin for local development.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(groups_bp)
app.register_blueprint(settlements_bp)
app.register_blueprint(activity_logs_bp)
app.register_blueprint(reminders_bp)
app.register_blueprint(admin_bp)


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
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode())
            return jsonify(data)
    except Exception as e:
        print(f"DEBUG: Currency API Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="127.0.0.1", port=5000)
