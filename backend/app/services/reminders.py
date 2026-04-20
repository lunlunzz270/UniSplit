from ..core.database import SessionLocal
from ..repositories.groups import GroupRepository
from ..repositories.reminders import ReminderRepository
from ..repositories.users import UserRepository
from ..schemas.reminders import ReminderCreate


def create_reminder(group_id: int, sender_id: int, reminder_in: ReminderCreate):
    db = SessionLocal()
    try:
        group_repo = GroupRepository(db)
        user_repo = UserRepository(db)
        reminder_repo = ReminderRepository(db)

        group = group_repo.get_group_by_id(group_id)
        if not group:
            raise ValueError("Group not found")
        if not user_repo.get_user_by_id(sender_id):
            raise ValueError("Sender not found")
        if not user_repo.get_user_by_id(reminder_in.recipient_id):
            raise ValueError("Recipient not found")
        if not group_repo.get_group_member(group_id, sender_id):
            raise ValueError("Sender must belong to the group")
        if not group_repo.get_group_member(group_id, reminder_in.recipient_id):
            raise ValueError("Recipient must belong to the group")

        return reminder_repo.create_reminder(
            group_id=group_id,
            sender_id=sender_id,
            recipient_id=reminder_in.recipient_id,
            message=reminder_in.message,
            expense_id=reminder_in.expense_id,
        )
    finally:
        db.close()


def is_group_member(group_id: int, user_id: int) -> bool:
    db = SessionLocal()
    try:
        group_repo = GroupRepository(db)
        return group_repo.get_group_member(group_id, user_id) is not None
    finally:
        db.close()


def get_group_reminders(group_id: int, user_id: int, limit: int = 10, offset: int = 0):
    db = SessionLocal()
    try:
        group_repo = GroupRepository(db)
        if not group_repo.get_group_member(group_id, user_id):
            raise ValueError("User must belong to the group")
        return ReminderRepository(db).get_group_reminders(group_id, limit=limit, offset=offset)
    finally:
        db.close()


def get_unsettled_expenses_for_recipient(group_id: int, user_id: int, recipient_id: int):
    db = SessionLocal()
    try:
        from ..repositories.expenses import ExpenseRepository
        group_repo = GroupRepository(db)
        if not group_repo.get_group_member(group_id, user_id):
            raise ValueError("User must belong to the group")
        return ExpenseRepository(db).get_unsettled_expenses_for_recipient(group_id, user_id, recipient_id)
    finally:
        db.close()
