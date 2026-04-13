from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from ..services import list_expenses as list_expenses_service, record_expense
from ..services.auth import get_current_user_from_token

expenses_bp = Blueprint("expenses", __name__)


def _extract_session_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    return request.headers.get("X-Session-Token") or request.headers.get("Authorization")


@expenses_bp.route("/api/expenses", methods=["GET"])
def get_expense_history():
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Session token is required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401
    
    current_user, _ = current
    
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    group_name = request.args.get("group_name", "").strip()
    
    expenses = list_expenses_service(
        user_id=current_user.id,
        is_admin=current_user.is_admin,
        search=search,
        category=category,
        group_name=group_name
    )
    return jsonify({"expenses": expenses}), 200


@expenses_bp.route("/api/expenses", methods=["POST"])
def create_expense():
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Login required to add expense"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401
    
    current_user, _ = current

    data = request.get_json(silent=True) or {}
    group_name = (data.get("group_name") or "").strip()
    description = (data.get("description") or "").strip()
    category = (data.get("category") or "").strip()
    payer_email = (data.get("payer_email") or "").strip().lower()
    participant_emails = data.get("participant_emails") or []

    try:
        amount = Decimal(str(data.get("amount", "0")).strip())
    except (InvalidOperation, ValueError):
        return jsonify({"error": "Invalid amount format"}), 400

    if not group_name or not description or not category or amount <= 0:
        return jsonify({"error": "Missing required fields or invalid amount"}), 400

    if not participant_emails:
        return jsonify({"error": "At least one participant is required"}), 400

    # Ensure the payer is the current authenticated user
    if payer_email and payer_email != current_user.email.lower():
        return jsonify({"error": f"Payer email mismatch. Authenticated as {current_user.email}"}), 403
    
    # Force use the authenticated user's email to avoid spoofing
    payer_email = current_user.email.lower()

    if isinstance(participant_emails, str):
        participant_emails = [item.strip() for item in participant_emails.replace("\n", ",").split(",")]

    try:
        expense = record_expense(
            group_name=group_name,
            description=description,
            amount=amount,
            category=category,
            payer_email=payer_email,
            participant_emails=participant_emails,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "id": expense.id,
            "group_id": expense.group_id,
            "description": expense.description,
            "amount": float(expense.amount),
            "category": expense.category,
        }
    ), 201


@expenses_bp.route("/api/expenses/summary", methods=["GET"])
def get_expense_summary():
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Session token is required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401
    
    current_user, _ = current
    
    expenses = list_expenses_service(
        user_id=current_user.id,
        is_admin=current_user.is_admin
    )
    
    total_amount = sum(float(e["amount"]) for e in expenses)
    category_map = {}
    for e in expenses:
        cat = e["category"]
        category_map[cat] = category_map.get(cat, 0) + float(e["amount"])
    
    return jsonify({
        "total_amount": total_amount,
        "count": len(expenses),
        "by_category": category_map,
        "is_admin_view": current_user.is_admin
    }), 200
