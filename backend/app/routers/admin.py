from flask import Blueprint, jsonify, request

from ..services.admin import list_users, set_user_active
from ..services.auth import get_current_user_from_token

admin_bp = Blueprint("admin", __name__)


def _extract_session_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    return request.headers.get("X-Session-Token")


def _require_admin():
    session_token = _extract_session_token()
    if not session_token:
        return None, (jsonify({"error": "Session token is required"}), 401)

    current = get_current_user_from_token(session_token)
    if not current:
        return None, (jsonify({"error": "Session expired or invalid"}), 401)

    current_user, _ = current
    if not current_user.is_admin:
        return None, (jsonify({"error": "Admin access required"}), 403)

    return current_user, None


def _user_to_dict(user):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
    }


@admin_bp.route("/api/admin/users", methods=["GET"])
def list_users_route():
    _, error = _require_admin()
    if error:
        return error
    users = list_users()
    return jsonify({"users": [_user_to_dict(user) for user in users]}), 200


@admin_bp.route("/api/admin/users/<int:user_id>/disable", methods=["POST"])
def disable_user_route(user_id: int):
    _, error = _require_admin()
    if error:
        return error
    try:
        user = set_user_active(user_id, False)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(_user_to_dict(user)), 200


@admin_bp.route("/api/admin/users/<int:user_id>/restore", methods=["POST"])
def restore_user_route(user_id: int):
    _, error = _require_admin()
    if error:
        return error
    try:
        user = set_user_active(user_id, True)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(_user_to_dict(user)), 200
