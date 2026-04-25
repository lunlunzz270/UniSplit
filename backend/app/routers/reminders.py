from flask import Blueprint, jsonify, request

from ..schemas.reminders import ReminderCreate
from ..services import create_reminder, get_group_reminders
from ..services.reminders import is_group_member, get_unsettled_expenses_for_recipient
from ..services.auth import get_current_user_from_token

reminders_bp = Blueprint("reminders", __name__)


def _extract_session_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    return request.headers.get("X-Session-Token")


def _reminder_to_dict(reminder):
    return {
        "id": reminder.id,
        "group_id": reminder.group_id,
        "group_name": reminder.group.name if reminder.group else "Unknown Group",
        "sender_id": reminder.sender_id,
        "sender_name": reminder.sender.full_name if reminder.sender else "Unknown",
        "sender_email": reminder.sender.email if reminder.sender else "N/A",
        "recipient_id": reminder.recipient_id,
        "recipient_name": reminder.recipient.full_name if reminder.recipient else "Unknown",
        "recipient_email": reminder.recipient.email if reminder.recipient else "N/A",
        "expense_id": reminder.expense_id,
        "expense_title": reminder.expense.description if reminder.expense else "No linked bill",
        "message": reminder.message,
        "is_read": reminder.is_read,
        "created_at": reminder.created_at.isoformat() if reminder.created_at else None,
    }


@reminders_bp.route("/api/groups/<int:group_id>/reminders", methods=["POST"])
def create_reminder_route(group_id: int):
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Session token is required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401

    current_user, _ = current
    if not is_group_member(group_id, current_user.id):
        return jsonify({"error": "Only group members can send reminders"}), 403

    data = request.get_json(silent=True) or {}
    try:
        reminder_in = ReminderCreate(**data)
        reminder = create_reminder(group_id, current_user.id, reminder_in)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(_reminder_to_dict(reminder)), 201


@reminders_bp.route("/api/groups/<int:group_id>/reminders", methods=["GET"])
def list_group_reminders_route(group_id: int):
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Session token is required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401

    current_user, _ = current
    limit = request.args.get("limit", 10, type=int)
    offset = request.args.get("offset", 0, type=int)
    try:
        reminders = get_group_reminders(group_id, current_user.id, limit=limit, offset=offset)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 403
    return jsonify({"reminders": [_reminder_to_dict(item) for item in reminders]}), 200


@reminders_bp.route("/api/groups/<int:group_id>/reminders/unsettled-expenses", methods=["GET"])
def list_unsettled_expenses_for_recipient_route(group_id: int):
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Session token is required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401

    current_user, _ = current
    recipient_id = request.args.get("recipient_id", type=int)
    if not recipient_id:
        return jsonify({"error": "recipient_id is required"}), 400

    try:
        expenses = get_unsettled_expenses_for_recipient(group_id, current_user.id, recipient_id)
        return jsonify({
            "expenses": [
                {
                    "id": e.id,
                    "description": e.description,
                    "amount": float(e.amount),
                    "date": e.created_at.isoformat() if e.created_at else None
                }
                for e in expenses
            ]
        }), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
