from sqlalchemy.orm import Session

from ..models.reminders import Reminder
from .activity_logs import ActivityLogRepository


class ReminderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_reminder(self, group_id: int, sender_id: int, recipient_id: int, message: str, expense_id: int = None) -> Reminder:
        reminder = Reminder(
            group_id=group_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            expense_id=expense_id,
            message=message,
        )
        self.db.add(reminder)
        self.db.flush()

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

    def get_group_reminders(self, group_id: int, limit: int = 10, offset: int = 0):
        return (
            self.db.query(Reminder)
            .filter(Reminder.group_id == group_id)
            .order_by(Reminder.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
