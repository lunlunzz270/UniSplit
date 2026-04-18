import logging
from bcrypt import gensalt, hashpw
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from ..core.database import SessionLocal
from ..models.activity_log import ActivityLog
from ..models.expenses import Expense, Settlement
from ..models.groups import Group
from ..models.users import User
from ..repositories.users import UserRepository

security_logger = logging.getLogger("security")


def _clamp_limit(limit: int | None, default: int = 20, maximum: int = 100) -> int:
    try:
        value = int(limit) if limit is not None else default
    except (TypeError, ValueError):
        value = default
    return max(1, min(value, maximum))


def _user_to_dict(user: User):
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


def list_users():
    db = SessionLocal()
    try:
        return UserRepository(db).list_users()
    finally:
        db.close()


def set_user_active(user_id: int, is_active: bool, performed_by_user_id: int | None = None):
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        updated = user_repo.set_user_active(user_id, is_active)
        action = "activated" if is_active else "disabled"
        security_logger.warning(
            "ADMIN_USER_%s | Actor: %s | Target: %s | Email: %s",
            action.upper(),
            performed_by_user_id or "unknown",
            updated.id,
            updated.email,
        )
        return updated
    finally:
        db.close()


def reset_user_password(
    user_id: int,
    new_password: str,
    performed_by_user_id: int | None = None,
    invalidate_sessions: bool = True,
):
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        password_hash = hashpw(new_password.encode("utf-8"), gensalt()).decode("utf-8")
        updated = user_repo.set_user_password(user_id, password_hash)
        cleared_sessions = user_repo.delete_sessions_for_user(user_id) if invalidate_sessions else 0

        security_logger.warning(
            "ADMIN_PASSWORD_RESET | Actor: %s | Target: %s | Email: %s | Sessions cleared: %s",
            performed_by_user_id or "unknown",
            updated.id,
            updated.email,
            cleared_sessions,
        )

        return {
            "user": _user_to_dict(updated),
            "sessions_cleared": cleared_sessions,
        }
    finally:
        db.close()


def get_system_overview():
    db = SessionLocal()
    try:
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_admins = db.query(func.count(User.id)).filter(User.is_admin.is_(True)).scalar() or 0
        total_transactions = db.query(func.count(Settlement.id)).scalar() or 0
        total_audit_logs = db.query(func.count(ActivityLog.id)).scalar() or 0
        latest_transaction = db.query(Settlement).order_by(Settlement.settled_at.desc().nullslast()).first()
        latest_audit = db.query(ActivityLog).order_by(ActivityLog.created_at.desc().nullslast()).first()
        return {
            "user_count": total_users,
            "active_user_count": db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0,
            "vip_count": db.query(func.count(User.id)).filter(User.is_vip.is_(True)).scalar() or 0,
            "total_settlements": total_transactions,
            "total_expenses": db.query(func.count(Expense.id)).scalar() or 0,
            "total_users": total_users,
            "total_admins": total_admins,
            "total_transactions": total_transactions,
            "total_audit_logs": total_audit_logs,
            "latest_transaction_at": latest_transaction.settled_at.isoformat() if latest_transaction and latest_transaction.settled_at else None,
            "latest_audit_at": latest_audit.created_at.isoformat() if latest_audit and latest_audit.created_at else None,
        }
    finally:
        db.close()


def list_system_transactions(limit: int | None = 20, search: str = ""):
    db = SessionLocal()
    try:
        query = (
            db.query(Settlement)
            .options(
                joinedload(Settlement.group),
                joinedload(Settlement.expense),
                joinedload(Settlement.payer),
                joinedload(Settlement.payee),
            )
            .order_by(Settlement.settled_at.desc().nullslast(), Settlement.id.desc())
        )

        if search:
            like = f"%{search}%"
            query = (
                query.join(Group, Settlement.group_id == Group.id)
                .join(User, Settlement.payer_id == User.id)
                .filter(
                    or_(
                        Group.name.ilike(like),
                        User.full_name.ilike(like),
                        Settlement.note.ilike(like),
                    )
                )
            )

        rows = query.limit(_clamp_limit(limit)).all()
        return [
            {
                "id": row.id,
                "group_id": row.group_id,
                "group_name": row.group.name if row.group else None,
                "expense_id": row.expense_id,
                "expense_description": row.expense.description if row.expense else None,
                "payer_id": row.payer_id,
                "payer_name": row.payer.full_name if row.payer else None,
                "payer_email": row.payer.email if row.payer else None,
                "payee_id": row.payee_id,
                "payee_name": row.payee.full_name if row.payee else None,
                "payee_email": row.payee.email if row.payee else None,
                "amount": float(row.amount),
                "status": row.status,
                "note": row.note,
                "settled_at": row.settled_at.isoformat() if row.settled_at else None,
            }
            for row in rows
        ]
    finally:
        db.close()


def list_system_audit_logs(limit: int | None = 20, search: str = ""):
    db = SessionLocal()
    try:
        query = (
            db.query(ActivityLog)
            .options(joinedload(ActivityLog.group), joinedload(ActivityLog.user))
            .order_by(ActivityLog.created_at.desc().nullslast(), ActivityLog.id.desc())
        )

        if search:
            like = f"%{search}%"
            query = (
                query.join(Group, ActivityLog.group_id == Group.id)
                .join(User, ActivityLog.user_id == User.id)
                .filter(
                    or_(
                        Group.name.ilike(like),
                        User.full_name.ilike(like),
                        User.email.ilike(like),
                        ActivityLog.action_type.ilike(like),
                        ActivityLog.description.ilike(like),
                    )
                )
            )

        rows = query.limit(_clamp_limit(limit)).all()
        return [
            {
                "id": row.id,
                "group_id": row.group_id,
                "group_name": row.group.name if row.group else None,
                "user_id": row.user_id,
                "user_name": row.user.full_name if row.user else None,
                "user_email": row.user.email if row.user else None,
                "action_type": row.action_type,
                "description": row.description,
                "ref_id": row.ref_id,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    finally:
        db.close()
