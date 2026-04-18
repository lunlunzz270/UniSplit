from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_

from ..models.expenses import Expense, ExpenseParticipant
from ..models.groups import Group, GroupMember
from ..models.users import User
from ..schemas.expenses import ExpenseCreate
from .activity_logs import ActivityLogRepository


class ExpenseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_expense_with_splits(self, group_id: int, expense_in: ExpenseCreate) -> Expense:
        """Use a database transaction to save both the main expense and split details simultaneously."""
        try:
            participant_ids = [p.user_id for p in expense_in.participants]
            if len(participant_ids) != len(set(participant_ids)):
                raise ValueError("Duplicate participants are not allowed")

            group_member_ids = {
                row[0]
                for row in self.db.query(GroupMember.user_id)
                .filter(GroupMember.group_id == group_id)
                .all()
            }
            if not set(participant_ids).issubset(group_member_ids):
                raise ValueError("All participants must belong to the group")
            if expense_in.paid_by not in group_member_ids:
                raise ValueError("Payer must belong to the group")

            total_share = sum(p.share for p in expense_in.participants)
            if total_share > expense_in.amount:
                raise ValueError("Total participant shares cannot exceed the expense amount")

            # 1. Create the main expense record
            db_expense = Expense(
                group_id=group_id,
                description=expense_in.description,
                amount=expense_in.amount,
                paid_by=expense_in.paid_by,
                category=expense_in.category
            )
            self.db.add(db_expense)
            # Use flush() instead of commit() to generate the db_expense.id for foreign keys
            # without permanently writing to the database yet.
            self.db.flush()

            # 2. Iterate and create specific split details for each participant
            for participant_data in expense_in.participants:
                db_participant = ExpenseParticipant(
                    expense_id=db_expense.id,  # Link to the newly generated expense ID
                    user_id=participant_data.user_id,
                    share=participant_data.share,
                    is_settled=False
                )
                self.db.add(db_participant)

            ActivityLogRepository(self.db).create_log(
                group_id=group_id,
                user_id=expense_in.paid_by,
                action_type="expense_added",
                description=f"Expense '{expense_in.description}' added",
                ref_id=db_expense.id,
            )

            # 3. If all steps succeed, commit the entire transaction
            self.db.commit()
            self.db.refresh(db_expense)
            return db_expense

        except SQLAlchemyError as e:
            # If any database error occurs (e.g., foreign key violation), rollback everything
            # to maintain ledger consistency.
            self.db.rollback()
            raise e
        except ValueError:
            self.db.rollback()
            raise

    def get_group_expenses(self, group_id: int):
        """Fetch all expense history for a specific group."""
        return self.db.query(Expense).filter(Expense.group_id == group_id).order_by(Expense.created_at.desc()).all()

    def update_participant_status(self, expense_id: int, user_id: int, status: str, appeal_reason: str | None = None) -> bool:
        """Update a participant's status (accepted/rejected) for an expense."""
        participant = (
            self.db.query(ExpenseParticipant)
            .filter(ExpenseParticipant.expense_id == expense_id, ExpenseParticipant.user_id == user_id)
            .first()
        )
        if not participant:
            return False

        participant.status = status
        if status == "rejected":
            participant.appeal_reason = appeal_reason

        self.db.commit()
        self.db.refresh(participant)
        return True

    def resolve_appeal(self, expense_id: int, user_id: int, action: str) -> bool:
        """Allow Payer to acknowledge or dismiss an appeal from a participant."""
        participant = (
            self.db.query(ExpenseParticipant)
            .filter(ExpenseParticipant.expense_id == expense_id, ExpenseParticipant.user_id == user_id)
            .first()
        )
        if not participant or participant.status != "rejected":
            return False

        if action == "dismiss":
            participant.status = "pending" # Send back to pending for reconsideration
        elif action == "acknowledge":
            participant.status = "appealed_acknowledged" # Mark as 'In Negotiation'

        self.db.commit()
        return True

    def list_expenses(self, user_id: int | None = None, is_admin: bool = False, search: str = "", category: str = "", group_name: str = "", start_date: str = "", end_date: str = ""):
        """Fetch expenses with optional filters, including date range."""
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

        if not is_admin and user_id is not None:
            # For non-admin, filter expenses where user is the payer OR a participant
            query = query.outerjoin(ExpenseParticipant, Expense.id == ExpenseParticipant.expense_id).filter(
                or_(
                    Expense.paid_by == user_id,
                    ExpenseParticipant.user_id == user_id
                )
            ).distinct()

        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    Expense.description.ilike(like),
                    User.full_name.ilike(like),
                    User.email.ilike(like),
                    Group.name.ilike(like),
                    Expense.participants.any(ExpenseParticipant.user.has(User.email.ilike(like)))
                )
            )

        if category:
            query = query.filter(Expense.category == category)

        if group_name:
            query = query.filter(Group.name.ilike(f"%{group_name}%"))

        if start_date:
            query = query.filter(Expense.created_at >= start_date)

        if end_date:
            # Append 23:59:59 to include the full end day
            query = query.filter(Expense.created_at <= f"{end_date} 23:59:59")

        rows = query.order_by(Expense.created_at.desc()).all()
        return [
            {
                "id": expense.id,
                "description": expense.description,
                "amount": float(expense.amount),
                "category": expense.category,
                "group_id": expense.group_id,
                "group_name": expense.group.name if expense.group else None,
                "payer_id": expense.paid_by,
                "payer": expense.payer.full_name if expense.payer else None,
                "date": expense.created_at.isoformat() if expense.created_at else None,
                "notes": "",
                "participants": [
                    {
                        "id": participant.id,
                        "user_id": participant.user_id,
                        "name": participant.user.full_name if participant.user else None,
                        "email": participant.user.email if participant.user else None,
                        "share": float(participant.share),
                        "status": participant.status,
                        "appeal_reason": participant.appeal_reason,
                        "is_settled": participant.is_settled,
                    }
                    for participant in expense.participants
                ],
            }
            for expense in rows
        ]
