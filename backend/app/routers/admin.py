from flask import Blueprint, jsonify, request

from ..services.admin import (
    get_system_overview,
    list_billing_transactions,
    list_system_audit_logs,
    list_system_transactions,
    list_users,
    reset_user_password,
    set_user_active,
)
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
        "role": "admin" if user.is_admin else "user",
        "balance": float(user.balance) if user.balance is not None else 0.0,
        "is_vip": user.is_vip,
        "vip_expiry": user.vip_expiry.isoformat() if user.vip_expiry else None,
    }


@admin_bp.route("/api/admin/users", methods=["GET"])
def list_users_route():
    _, error = _require_admin()
    if error:
        return error
    users = list_users()
    return jsonify({"users": [_user_to_dict(user) for user in users]}), 200


@admin_bp.route("/api/admin/overview", methods=["GET"])
def overview_route():
    _, error = _require_admin()
    if error:
        return error
    return jsonify(get_system_overview()), 200


@admin_bp.route("/api/admin/summary", methods=["GET"])
def summary_route():
    return overview_route()


@admin_bp.route("/api/admin/system/transactions", methods=["GET"])
def system_transactions_route():
    _, error = _require_admin()
    if error:
        return error
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)
    search = request.args.get("search", "").strip()
    return jsonify({"transactions": list_system_transactions(limit=limit, offset=offset, search=search)}), 200


@admin_bp.route("/api/admin/system-transactions", methods=["GET"])
def system_transactions_alias_route():
    return system_transactions_route()


@admin_bp.route("/api/admin/billing-transactions", methods=["GET"])
def list_billing_transactions_route():
    try:
        _, error = _require_admin()
        if error:
            return error
        
        trans_type = request.args.get("type") # recharge or membership
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)
        search = request.args.get("search", "").strip()
        
        return jsonify(list_billing_transactions(type=trans_type, page=page, limit=limit, search=search)), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/api/admin/system/audit-logs", methods=["GET"])
def system_audit_logs_route():
    _, error = _require_admin()
    if error:
        return error
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)
    search = request.args.get("search", "").strip()
    return jsonify({"audit_logs": list_system_audit_logs(limit=limit, offset=offset, search=search)}), 200


@admin_bp.route("/api/admin/system-activity", methods=["GET"])
def system_activity_alias_route():
    _, error = _require_admin()
    if error:
        return error
    limit = request.args.get("limit", 20)
    search = request.args.get("search", "").strip()
    return jsonify({"activity_logs": list_system_audit_logs(limit=limit, search=search)}), 200


@admin_bp.route("/api/admin/users/<int:user_id>/disable", methods=["POST"])
def disable_user_route(user_id: int):
    current_user, error = _require_admin()
    if error:
        return error
    try:
        user = set_user_active(user_id, False, performed_by_user_id=current_user.id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    payload = _user_to_dict(user)
    payload["message"] = "User disabled successfully"
    return jsonify(payload), 200


@admin_bp.route("/api/admin/users/<int:user_id>/restore", methods=["POST"])
def restore_user_route(user_id: int):
    current_user, error = _require_admin()
    if error:
        return error
    try:
        user = set_user_active(user_id, True, performed_by_user_id=current_user.id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    payload = _user_to_dict(user)
    payload["message"] = "User restored successfully"
    return jsonify(payload), 200


@admin_bp.route("/api/admin/users/<int:user_id>/reset-password", methods=["POST"])
def reset_password_route(user_id: int):
    current_user, error = _require_admin()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    new_password = (data.get("new_password") or "").strip()
    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    try:
        result = reset_user_password(
            user_id,
            new_password,
            performed_by_user_id=current_user.id,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({
        "message": "Password reset successfully",
        **result,
    }), 200
