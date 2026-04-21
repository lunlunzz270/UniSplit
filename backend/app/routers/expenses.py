from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request, make_response

from ..services import export_expenses_csv, list_expenses as list_expenses_service, record_expense, respond_to_expense, resolve_expense_appeal
from ..services.auth import get_current_user_from_token

expenses_bp = Blueprint("expenses", __name__)


def _extract_session_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ").strip()
    return request.headers.get("X-Session-Token") or request.headers.get("Authorization")


def _get_current_user():
    session_token = _extract_session_token()
    if not session_token:
        return None, (jsonify({"error": "Session token is required"}), 401)

    current = get_current_user_from_token(session_token)
    if not current:
        return None, (jsonify({"error": "Session expired or invalid"}), 401)

    return current, None


@expenses_bp.route("/api/expenses/<int:expense_id>/respond", methods=["POST"])
def respond_to_expense_route(expense_id: int):
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Login required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401
    
    current_user, _ = current
    data = request.get_json(silent=True) or {}
    status = data.get("status") # accepted or rejected
    appeal_reason = data.get("appeal_reason")

    if status not in ["accepted", "rejected"]:
        return jsonify({"error": "Invalid status. Must be 'accepted' or 'rejected'"}), 400

    try:
        success = respond_to_expense(
            expense_id=expense_id,
            user_id=current_user.id,
            status=status,
            appeal_reason=appeal_reason
        )
        return jsonify({"success": success, "status": status}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

@expenses_bp.route("/api/expenses/<int:expense_id>/resolve_appeal", methods=["POST"])
def resolve_appeal_route(expense_id: int):
    session_token = _extract_session_token()
    if not session_token:
        return jsonify({"error": "Login required"}), 401

    current = get_current_user_from_token(session_token)
    if not current:
        return jsonify({"error": "Session expired or invalid"}), 401
    
    data = request.get_json(silent=True) or {}
    participant_id = data.get("participant_id")
    action = data.get("action") # acknowledge or dismiss

    if not participant_id or action not in ["acknowledge", "dismiss"]:
        return jsonify({"error": "participant_id and valid action required"}), 400

    try:
        success = resolve_expense_appeal(expense_id, participant_id, action)
        return jsonify({"success": success}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@expenses_bp.route("/api/expenses", methods=["GET"])
def get_expense_history():
    current, error = _get_current_user()
    if error:
        return error
    current_user, _ = current
    
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    group_name = request.args.get("group_name", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    limit = request.args.get("limit", 10, type=int)
    offset = request.args.get("offset", 0, type=int)
    
    expenses = list_expenses_service(
        user_id=current_user.id,
        is_admin=current_user.is_admin,
        search=search,
        category=category,
        group_name=group_name,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    return jsonify({"expenses": expenses}), 200


@expenses_bp.route("/api/expenses/export", methods=["GET"])
def export_expense_history():
    current, error = _get_current_user()
    if error:
        return error

    current_user, _ = current
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    group_name = request.args.get("group_name", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    csv_content = export_expenses_csv(
        user_id=current_user.id,
        is_admin=current_user.is_admin,
        search=search,
        category=category,
        group_name=group_name,
        start_date=start_date,
        end_date=end_date,
    )

    response = make_response(csv_content)
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = 'attachment; filename="expense_report.csv"'
    return response


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
