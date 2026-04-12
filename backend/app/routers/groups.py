from flask import Blueprint, jsonify, request

from ..schemas.groups import GroupCreate
from ..services import add_user_to_group, can_manage_group, create_group, get_user_groups
from ..services.auth import get_current_user_from_token

groups_bp = Blueprint("groups", __name__)


def _group_to_dict(group):
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "created_by": group.created_by,
    }


def _member_to_dict(member):
    return {
        "id": member.id,
        "group_id": member.group_id,
        "user_id": member.user_id,
        "role": member.role,
    }


def _extract_session_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    return request.headers.get("X-Session-Token")


@groups_bp.route("/api/groups", methods=["POST"])
def create_group_route():
    data = request.get_json(silent=True) or {}
    creator_id = data.get("creator_id")
    session_token = _extract_session_token()
    current = get_current_user_from_token(session_token) if session_token else None
    if session_token and not current:
        return jsonify({"error": "Session expired or invalid"}), 401
    if creator_id is None:
        if not current:
            return jsonify({"error": "creator_id or valid session token is required"}), 401
        creator_id = current[0].id
    elif current and int(creator_id) != current[0].id:
        return jsonify({"error": "creator_id must match the authenticated user"}), 403
    if creator_id is None:
        return jsonify({"error": "creator_id is required"}), 400

    try:
        group_in = GroupCreate(**data)
        group_in = GroupCreate(name=group_in.name, description=group_in.description)
        group = create_group(group_in, int(creator_id))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid creator_id"}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(_group_to_dict(group)), 201


@groups_bp.route("/api/users/<int:user_id>/groups", methods=["GET"])
def list_user_groups(user_id: int):
    session_token = _extract_session_token()
    current = get_current_user_from_token(session_token) if session_token else None
    if session_token and not current:
        return jsonify({"error": "Session expired or invalid"}), 401
    if current and current[0].id != user_id:
        return jsonify({"error": "You can only view your own groups"}), 403
    groups = get_user_groups(user_id)
    return jsonify({"groups": [_group_to_dict(group) for group in groups]}), 200


@groups_bp.route("/api/groups/<int:group_id>/members", methods=["POST"])
def add_group_member(group_id: int):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    session_token = _extract_session_token()
    current = get_current_user_from_token(session_token) if session_token else None
    if session_token and not current:
        return jsonify({"error": "Session expired or invalid"}), 401
    if not current:
        return jsonify({"error": "Session token is required"}), 401
    if not can_manage_group(group_id, current[0].id):
        return jsonify({"error": "Only the group owner or admin can add members"}), 403
    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    try:
        member = add_user_to_group(group_id=group_id, user_id=int(user_id), role="MEMBER")
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user_id"}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(_member_to_dict(member)), 201
