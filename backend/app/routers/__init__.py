from flask import Blueprint, request, jsonify
import logging

from ..services.auth import (
    create_session_for_user,
    create_user,
    get_current_user_from_token,
    get_user_by_email,
    logout_session,
    serialize_user,
    verify_password,
)
from ..services.redemption import redeem_code, buy_membership_with_balance
from ..services.groups import join_group, leave_group
from .expenses import expenses_bp
from .groups import groups_bp
from .settlements import settlements_bp
from .activity_logs import activity_logs_bp
from .reminders import reminders_bp
from .admin import admin_bp

auth_bp = Blueprint('auth', __name__)
security_logger = logging.getLogger("security")


def _extract_session_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    return (
        request.headers.get("X-Session-Token")
        or (request.get_json(silent=True) or {}).get("session_token")
        or (request.get_json(silent=True) or {}).get("token")
    )


@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    email = data.get('email', '').lower()
    password = data.get('password')

    if not name or not email or not password:
        security_logger.warning(f"AUTH_REGISTER_FAIL | Failure | Missing fields for email: {email}")
        return jsonify({'error': 'All fields are required'}), 400

    if get_user_by_email(email):
        security_logger.warning(f"AUTH_REGISTER_FAIL | Failure | Email already exists: {email}")
        return jsonify({'error': 'Email already registered'}), 400

    user = create_user(name, email, password)
    session = create_session_for_user(user.id)
    security_logger.info(f"AUTH_REGISTER_SUCCESS | Success | User ID: {user.id} | Email: {email}")
    return jsonify(serialize_user(user, session)), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').lower()
    password = data.get('password')

    user = get_user_by_email(email)
    if not user or not user.is_active or not verify_password(password, user.password):
        security_logger.warning(f"AUTH_LOGIN_FAIL | Failure | Attempted email: {email}")
        return jsonify({'error': 'Invalid email or password'}), 401

    session = create_session_for_user(user.id)
    security_logger.info(f"AUTH_LOGIN_SUCCESS | Success | User ID: {user.id} | Email: {email}")
    return jsonify(serialize_user(user, session)), 200


@auth_bp.route('/api/me', methods=['GET'])
@auth_bp.route('/api/session', methods=['GET'])
def current_user():
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Session token is required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        security_logger.warning(f"SESSION_AUTH_FAIL | Failure | Invalid token attempt")
        return jsonify({"error": "Session expired or invalid"}), 401

    user, session = current
    return jsonify(serialize_user(user, session)), 200


@auth_bp.route('/api/redeem', methods=['POST'])
def redeem():
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Session token is required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401

    user, _ = current
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    if not code:
        return jsonify({"error": "Redemption code is required"}), 400

    try:
        result = redeem_code(user.id, code)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@auth_bp.route('/api/membership/buy', methods=['POST'])
def buy_membership():
    session_token = _extract_session_token()
    current = get_current_user_from_token(session_token) if session_token else None
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401

    user, _ = current
    data = request.get_json(silent=True) or {}
    plan = data.get("plan") # monthly or yearly
    try:
        result = buy_membership_with_balance(user.id, plan)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@auth_bp.route('/api/logout', methods=['POST', 'DELETE'])
def logout():
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Session token is required"}), 401

    if not logout_session(session_token):
        security_logger.warning(f"AUTH_LOGOUT_FAIL | Failure | Token not found during logout")
        return jsonify({"error": "Session not found"}), 404

    security_logger.info(f"AUTH_LOGOUT_SUCCESS | Success | Session invalidated")
    return jsonify({"message": "Logged out"}), 200


def _require_current_user_or_400():
    session_token = _extract_session_token()
    if not session_token:
        return None, jsonify({"error": "Session token is required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return None, jsonify({"error": "Session expired or invalid"}), 401
    return current, None, None


@groups_bp.route("/api/groups/<int:group_id>/join", methods=["POST"])
def join_group_route(group_id: int):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    session_token = _extract_session_token()
    current = get_current_user_from_token(session_token) if session_token else None
    if session_token and not current:
        return jsonify({"error": "Session expired or invalid"}), 401
    if user_id is None:
        current, error_response, status_code = _require_current_user_or_400()
        if error_response:
            return error_response, status_code
        user_id = current[0].id
    elif current and int(user_id) != current[0].id:
        security_logger.warning(f"AUTHZ_VIOLATION | Failure | User {current[0].id} tried to join group as user {user_id}")
        return jsonify({"error": "user_id must match the authenticated user"}), 403

    try:
        member, created = join_group(group_id=group_id, user_id=int(user_id))
        return jsonify({"member": member, "created": created}), (201 if created else 200)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@groups_bp.route("/api/groups/<int:group_id>/leave", methods=["POST", "DELETE"])
def leave_group_route(group_id: int):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    session_token = _extract_session_token()
    current = get_current_user_from_token(session_token) if session_token else None
    if session_token and not current:
        return jsonify({"error": "Session expired or invalid"}), 401
    if user_id is None:
        current, error_response, status_code = _require_current_user_or_400()
        if error_response:
            return error_response, status_code
        user_id = current[0].id
    elif current and int(user_id) != current[0].id:
        security_logger.warning(f"AUTHZ_VIOLATION | Failure | User {current[0].id} tried to leave group as user {user_id}")
        return jsonify({"error": "user_id must match the authenticated user"}), 403

    try:
        result = leave_group(group_id=group_id, user_id=int(user_id))
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
