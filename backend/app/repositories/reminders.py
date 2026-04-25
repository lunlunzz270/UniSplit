from sqlalchemy.orm import Session, joinedload

from ..models.reminders import Reminder
from .activity_logs import ActivityLogRepository


class ReminderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_reminder(self, group_id: int, sender_id: int, recipient_id: int, message: str, expense_id: int = None, log_description: str = None) -> Reminder:
        reminder = Reminder(
            group_id=group_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            expense_id=expense_id,
            message=message,
        )
        self.db.add(reminder)
        self.db.flush()

        if not log_description:
            log_description = f"Reminder sent to user {recipient_id}"
            if expense_id:
                log_description += f" for expense {expense_id}"

        ActivityLogRepository(self.db).create_log(
            group_id=group_id,
            user_id=sender_id,
            action_type="reminder_created",
            description=log_description,
            ref_id=reminder.id,
        )

        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def get_group_reminders(self, group_id: int, user_id: int, is_admin: bool = False, limit: int = 10, offset: int = 0):
        query = self.db.query(Reminder).options(
            joinedload(Reminder.group),
            joinedload(Reminder.sender),
            joinedload(Reminder.recipient),
            joinedload(Reminder.expense),
        ).filter(Reminder.group_id == group_id)

        if not is_admin:
            # Regular users only see reminders related to them
            from sqlalchemy import or_
            query = query.filter(or_(
                Reminder.sender_id == user_id,
                Reminder.recipient_id == user_id
            ))

        return (
            query.order_by(Reminder.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
