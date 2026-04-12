from flask import Blueprint, jsonify, request

from ..schemas.settlements import SettlementCreate
from ..services import create_settlement, get_group_settlements
from ..services.auth import get_current_user_from_token

settlements_bp = Blueprint("settlements", __name__)

def _extract_session_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    return request.headers.get("X-Session-Token")

def _settlement_to_dict(settlement):
    return {
        "id": settlement.id,
        "group_id": settlement.group_id,
        "payer_id": settlement.payer_id,
        "payee_id": settlement.payee_id,
        "amount": float(settlement.amount),
        "note": settlement.note,
        "settled_at": settlement.settled_at.isoformat() if settlement.settled_at else None,
    }


@settlements_bp.route("/api/groups/<int:group_id>/settlements", methods=["POST"])
def create_settlement_route(group_id: int):
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Session token is required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401

    data = request.get_json(silent=True) or {}
    try:
        settlement_in = SettlementCreate(**data)
        settlement = create_settlement(group_id, settlement_in)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(_settlement_to_dict(settlement)), 201


@settlements_bp.route("/api/groups/<int:group_id>/settlements", methods=["GET"])
def list_group_settlements(group_id: int):
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Session token is required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401

    settlements = get_group_settlements(group_id)
    return jsonify({"settlements": [_settlement_to_dict(item) for item in settlements]}), 200
