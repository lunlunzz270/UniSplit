from flask import Blueprint, jsonify, request

from ..services import get_group_activity_logs
from ..services.auth import get_current_user_from_token

activity_logs_bp = Blueprint("activity_logs", __name__)

def _extract_session_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    return request.headers.get("X-Session-Token")

@activity_logs_bp.route("/api/groups/<int:group_id>/activity-logs", methods=["GET"])
def list_group_activity_logs(group_id: int):
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Session token is required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401

    logs = get_group_activity_logs(group_id)
    return jsonify({"activity_logs": logs}), 200
