from ..core.database import SessionLocal
from ..repositories.groups import GroupRepository
from ..repositories.reminders import ReminderRepository
from ..repositories.users import UserRepository
from ..models.reminders import Reminder
from ..models.expenses import Expense, ExpenseParticipant
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

        # Logic Check: Only allow reminders if there is actual unsettled debt
        from ..repositories.expenses import ExpenseRepository
        expense_repo = ExpenseRepository(db)
        
        if reminder_in.expense_id:
            # Check specific bill
            expense = db.query(Expense).filter(Expense.id == reminder_in.expense_id).first()
            if not expense or expense.group_id != group_id:
                raise ValueError("Linked bill not found in this group")
            
            # Check if this recipient actually owes for this bill
            p = db.query(ExpenseParticipant).filter_by(
                expense_id=reminder_in.expense_id, 
                user_id=reminder_in.recipient_id
            ).first()
            if not p or p.is_settled or p.status == 'paid':
                raise ValueError("This bill is already settled for this recipient")
        else:
            # Check if there is ANY unsettled debt from recipient to sender in this group
            unsettled = expense_repo.get_unsettled_expenses_for_recipient(
                group_id, sender_id, reminder_in.recipient_id
            )
            if not unsettled:
                raise ValueError("This member has no unsettled debt to you in this group. Reminder cannot be sent.")

        # Build detailed log description
        recipient = user_repo.get_user_by_id(reminder_in.recipient_id)
        recipient_info = f"{recipient.full_name} ({recipient.email})"
        log_desc = f"Reminder sent to {recipient_info}"
        
        if reminder_in.expense_id:
            # We already fetched 'expense' above if reminder_in.expense_id exists
            # but let's make sure it's accessible or re-fetch
            expense = db.query(Expense).filter(Expense.id == reminder_in.expense_id).first()
            if expense:
                log_desc += f" for bill '{expense.description}'"

        reminder = reminder_repo.create_reminder(
            group_id=group_id,
            sender_id=sender_id,
            recipient_id=reminder_in.recipient_id,
            message=reminder_in.message,
            expense_id=reminder_in.expense_id,
            log_description=log_desc
        )

        # Re-fetch with joinedload to ensure all relationships are available after session close
        from sqlalchemy.orm import joinedload
        return (
            db.query(Reminder)
            .options(
                joinedload(Reminder.group),
                joinedload(Reminder.sender),
                joinedload(Reminder.recipient),
                joinedload(Reminder.expense),
            )
            .filter(Reminder.id == reminder.id)
            .first()
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
        user_repo = UserRepository(db)
        
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if not group_repo.get_group_member(group_id, user_id):
            raise ValueError("User must belong to the group")
        
        return ReminderRepository(db).get_group_reminders(
            group_id=group_id, 
            user_id=user_id, 
            is_admin=user.is_admin, 
            limit=limit, 
            offset=offset
        )
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
