from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from ..services import list_expenses as list_expenses_service, record_expense

expenses_bp = Blueprint("expenses", __name__)


@expenses_bp.route("/api/expenses", methods=["GET"])
def get_expense_history():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    group_name = request.args.get("group_name", "").strip()
    expenses = list_expenses_service(search=search, category=category, group_name=group_name)
    return jsonify({"expenses": expenses}), 200


@expenses_bp.route("/api/expenses", methods=["POST"])
def create_expense():
    data = request.get_json(silent=True) or {}
    group_name = (data.get("group_name") or "").strip()
    description = (data.get("description") or "").strip()
    category = (data.get("category") or "").strip()
    payer_email = (data.get("payer_email") or "").strip().lower()
    participant_emails = data.get("participant_emails") or []

    try:
        amount = Decimal(str(data.get("amount", "")).strip())
    except (InvalidOperation, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    if not group_name or not description or not category or not payer_email:
        return jsonify({"error": "Group, description, category, payer, and amount are required"}), 400

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
