from ..core.database import SessionLocal
from ..repositories.groups import GroupRepository
from ..repositories.users import UserRepository
from ..repositories.settlements import SettlementRepository
from ..repositories.expenses import ExpenseRepository
from ..schemas.settlements import SettlementCreate


def create_settlement(group_id: int, settlement_in: SettlementCreate):
    db = SessionLocal()
    try:
        group_repo = GroupRepository(db)
        user_repo = UserRepository(db)
        expense_repo = ExpenseRepository(db)

        # 1. Basic validation
        if settlement_in.payer_id == settlement_in.payee_id:
            raise ValueError("Payer and payee must be different users")

        # 2. Group membership validation
        payer_groups = {group.id for group in group_repo.get_user_groups(settlement_in.payer_id)}
        payee_groups = {group.id for group in group_repo.get_user_groups(settlement_in.payee_id)}

        if group_id not in payer_groups:
            raise ValueError("Payer must belong to the group")
        if group_id not in payee_groups:
            raise ValueError("Payee must belong to the group")

        # 3. Admin isolation check
        payer = user_repo.get_user_by_id(settlement_in.payer_id)
        if payer and payer.is_admin:
            raise ValueError("Administrators cannot participate in financial settlements.")

        # 4. Expense & Participant validation
        # Ensure the expense exists and belongs to this group
        expenses = expense_repo.get_group_expenses(group_id)
        expense_ids = {e.id for e in expenses}
        if settlement_in.expense_id not in expense_ids:
            raise ValueError("The specified expense does not exist in this group.")

        # 5. Call repository to perform atomic balance transfer and status update
        return SettlementRepository(db).create_settlement(group_id, settlement_in)
    finally:
        db.close()


def get_group_settlements(group_id: int):
    db = SessionLocal()
    try:
        return SettlementRepository(db).get_group_settlements(group_id)
    finally:
        db.close()
