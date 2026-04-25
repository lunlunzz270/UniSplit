from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from datetime import datetime, time

from ..models.expenses import Expense, ExpenseParticipant
from ..models.groups import Group, GroupMember
from ..models.users import User
from ..schemas.expenses import ExpenseCreate
from .activity_logs import ActivityLogRepository


class ExpenseRepository:
    def __init__(self, db: Session):
        self.db = db

    def _apply_date_filters(self, query, start_date: str = "", end_date: str = ""):
        if start_date:
            try:
                start_dt = datetime.combine(datetime.fromisoformat(start_date).date(), time.min)
                query = query.filter(Expense.created_at >= start_dt)
            except ValueError:
                pass

        if end_date:
            try:
                end_dt = datetime.combine(datetime.fromisoformat(end_date).date(), time.max)
                query = query.filter(Expense.created_at <= end_dt)
            except ValueError:
                pass

        return query

    def create_expense_with_splits(self, group_id: int, expense_in: ExpenseCreate) -> Expense:
        try:
            group = self.db.query(Group).filter(Group.id == group_id).first()
            if not group:
                raise ValueError("Group not found")

            member_ids = {
                member.user_id
                for member in self.db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
            }

            participant_ids = [p.user_id for p in expense_in.participants]
            if len(participant_ids) != len(set(participant_ids)):
                raise ValueError("Duplicate participants are not allowed")

            missing_participants = [user_id for user_id in participant_ids if user_id not in member_ids]
            if expense_in.paid_by not in member_ids:
                missing_participants.append(expense_in.paid_by)
            if missing_participants:
                raise ValueError("All participants must belong to the group")

            # 1. Create main expense
            db_expense = Expense(
                group_id=group_id,
                description=expense_in.description,
                amount=expense_in.amount,
                paid_by=expense_in.paid_by,
                category=expense_in.category
            )
            self.db.add(db_expense)
            self.db.flush()

            # 2. Create participants
            for p_data in expense_in.participants:
                db_p = ExpenseParticipant(
                    expense_id=db_expense.id,
                    user_id=p_data.user_id,
                    share=p_data.share,
                    is_settled=False
                )
                self.db.add(db_p)

            ActivityLogRepository(self.db).create_log(
                group_id=group_id,
                user_id=expense_in.paid_by,
                action_type="expense_added",
                description=f"Expense '{expense_in.description}' added",
                ref_id=db_expense.id,
            )
            self.db.commit()
            self.db.refresh(db_expense)
            return db_expense
        except Exception as e:
            self.db.rollback()
            raise e

    def list_expenses(self, user_id=None, is_admin=False, search="", category="", group_name="", start_date="", end_date="", limit=10, offset=0):
        participant_user = aliased(User)
        joined_participants = False
        query = (
            self.db.query(Expense)
            .options(
                joinedload(Expense.group),
                joinedload(Expense.payer),
                joinedload(Expense.participants).joinedload(ExpenseParticipant.user),
            )
            .join(Group, Expense.group_id == Group.id)
            .join(User, Expense.paid_by == User.id)
        )

        if not is_admin and user_id:
            query = query.outerjoin(ExpenseParticipant, Expense.id == ExpenseParticipant.expense_id).filter(
                or_(Expense.paid_by == user_id, ExpenseParticipant.user_id == user_id)
            ).distinct()
            joined_participants = True

        if search:
            if not joined_participants:
                query = query.outerjoin(ExpenseParticipant, Expense.id == ExpenseParticipant.expense_id)
                joined_participants = True
            query = query.outerjoin(participant_user, ExpenseParticipant.user_id == participant_user.id)
            like = f"%{search}%"
            query = query.filter(
                or_(
                    Expense.description.ilike(like),
                    Expense.category.ilike(like),
                    Group.name.ilike(like),
                    User.full_name.ilike(like),
                    User.email.ilike(like),
                    participant_user.full_name.ilike(like),
                    participant_user.email.ilike(like),
                )
            )
        if category:
            query = query.filter(Expense.category == category)
        if group_name:
            query = query.filter(Group.name.ilike(f"%{group_name}%"))
        query = self._apply_date_filters(query, start_date=start_date, end_date=end_date)
        
        # Order and paginate
        query = query.order_by(Expense.created_at.desc())
        if offset:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        
        rows = query.all()
        return [
            {
                "id": e.id,
                "description": e.description,
                "amount": float(e.amount),
                "category": e.category,
                "group_name": e.group.name if e.group else "Unknown",
                "group_id": e.group_id,
                "payer_id": e.paid_by,
                "payer": e.payer.full_name if e.payer else "Unknown",
                "payer_email": e.payer.email if e.payer else "N/A",
                "date": e.created_at.isoformat() if e.created_at else None,
                "participants": [
                    {
                        "user_id": p.user_id,
                        "name": p.user.full_name,
                        "email": p.user.email,
                        "share": float(p.share),
                        "status": p.status,
                        "is_settled": p.is_settled,
                        "appeal_reason": p.appeal_reason
                    }
                    for p in e.participants
                ]
            } for e in rows
        ]

    def get_group_expenses(self, group_id: int):
        return (
            self.db.query(Expense)
            .options(
                joinedload(Expense.group),
                joinedload(Expense.payer),
                joinedload(Expense.participants).joinedload(ExpenseParticipant.user),
            )
            .filter(Expense.group_id == group_id)
            .order_by(Expense.created_at.desc())
            .all()
        )

    def get_unsettled_expenses_for_recipient(self, group_id: int, payer_id: int, recipient_id: int):
        return (
            self.db.query(Expense)
            .join(ExpenseParticipant, Expense.id == ExpenseParticipant.expense_id)
            .filter(
                Expense.group_id == group_id,
                Expense.paid_by == payer_id,
                ExpenseParticipant.user_id == recipient_id,
                ExpenseParticipant.is_settled == False
            ).all()
        )

    def update_participant_status(self, expense_id, user_id, status, appeal_reason=None):
        p = self.db.query(ExpenseParticipant).filter_by(expense_id=expense_id, user_id=user_id).first()
        if not p: return False
        p.status = status
        if status == "rejected": p.appeal_reason = appeal_reason
        self.db.commit()
        return True

    def resolve_appeal(self, expense_id: int, user_id: int, action: str):
        p = self.db.query(ExpenseParticipant).filter_by(expense_id=expense_id, user_id=user_id).first()
        if not p:
            return False
        
        if action == "acknowledge":
            # Payer acknowledges the error
            p.status = "appealed_acknowledged"
        elif action == "dismiss":
            # Payer dismisses the appeal, forcing acceptance
            p.status = "accepted"
            p.appeal_reason = None
            
        self.db.commit()
        return True
