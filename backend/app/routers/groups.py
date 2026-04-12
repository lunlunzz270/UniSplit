from flask import Blueprint, jsonify, request

from ..schemas.groups import GroupCreate
from ..services import add_user_to_group, create_group, get_user_groups

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


@groups_bp.route("/api/groups", methods=["POST"])
def create_group_route():
    data = request.get_json(silent=True) or {}
    creator_id = data.get("creator_id")
    if creator_id is None:
        return jsonify({"error": "creator_id is required"}), 400

    try:
        group_in = GroupCreate(**data)
        group = create_group(group_in, int(creator_id))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid creator_id"}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(_group_to_dict(group)), 201


@groups_bp.route("/api/users/<int:user_id>/groups", methods=["GET"])
def list_user_groups(user_id: int):
    groups = get_user_groups(user_id)
    return jsonify({"groups": [_group_to_dict(group) for group in groups]}), 200


@groups_bp.route("/api/groups/<int:group_id>/members", methods=["POST"])
def add_group_member(group_id: int):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    role = (data.get("role") or "MEMBER").strip() or "MEMBER"
    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    try:
        member = add_user_to_group(group_id=group_id, user_id=int(user_id), role=role)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user_id"}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(_member_to_dict(member)), 201
