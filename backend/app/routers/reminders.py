from flask import Blueprint, jsonify, request

from ..schemas.reminders import ReminderCreate
from ..services import create_reminder, get_group_reminders
from ..services.reminders import is_group_member
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
        "sender_id": reminder.sender_id,
        "recipient_id": reminder.recipient_id,
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
    if not is_group_member(group_id, current_user.id):
        return jsonify({"error": "Only group members can view reminders"}), 403

    try:
        reminders = get_group_reminders(group_id, current_user.id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 403
    return jsonify({"reminders": [_reminder_to_dict(item) for item in reminders]}), 200
