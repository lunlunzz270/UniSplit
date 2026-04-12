from flask import Blueprint, jsonify

from ..services import get_group_activity_logs

activity_logs_bp = Blueprint("activity_logs", __name__)


@activity_logs_bp.route("/api/groups/<int:group_id>/activity-logs", methods=["GET"])
def list_group_activity_logs(group_id: int):
    logs = get_group_activity_logs(group_id)
    return jsonify({"activity_logs": logs}), 200
