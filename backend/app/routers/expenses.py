from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from ..core.database import SessionLocal
from ..models.expenses import Expense, Settlement
from ..models.groups import Group
from ..models.users import User

expenses_bp = Blueprint("expenses", __name__)


@expenses_bp.route("/api/expenses", methods=["GET"])
def list_expenses():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    group_name = request.args.get("group_name", "").strip()

    db = SessionLocal()
    try:
        query = (
            db.query(Expense, Group.name.label("group_name"), User.full_name.label("payer_name"))
            .join(Group, Expense.group_id == Group.id)
            .join(User, Expense.paid_by == User.id)
        )

        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    Expense.description.ilike(like),
                    User.full_name.ilike(like),
                    Group.name.ilike(like),
                )
            )

        if category:
            query = query.filter(Expense.category == category)

        if group_name:
            query = query.filter(Group.name.ilike(f"%{group_name}%"))

        rows = query.order_by(Expense.created_at.desc()).all()

        expenses = []
        for expense, group_name_value, payer_name in rows:
            expenses.append(
                {
                    "id": expense.id,
                    "description": expense.description,
                    "amount": float(expense.amount),
                    "category": expense.category,
                    "group_id": expense.group_id,
                    "group_name": group_name_value,
                    "payer": payer_name,
                    "date": expense.created_at.isoformat() if expense.created_at else None,
                    "notes": "",
                }
            )

        return jsonify({"expenses": expenses}), 200
    finally:
        db.close()
