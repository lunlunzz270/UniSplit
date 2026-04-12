from ..core.database import SessionLocal
from ..repositories.groups import GroupRepository
from ..repositories.users import UserRepository
from ..repositories.settlements import SettlementRepository
from ..schemas.settlements import SettlementCreate


def create_settlement(group_id: int, settlement_in: SettlementCreate):
    db = SessionLocal()
    try:
        group_repo = GroupRepository(db)
        user_repo = UserRepository(db)

        if settlement_in.payer_id == settlement_in.payee_id:
            raise ValueError("Payer and payee must be different users")

        payer_groups = {group.id for group in group_repo.get_user_groups(settlement_in.payer_id)}
        payee_groups = {group.id for group in group_repo.get_user_groups(settlement_in.payee_id)}

        if group_id not in payer_groups:
            raise ValueError("Payer must belong to the group")
        if not user_repo.get_user_by_id(settlement_in.payee_id):
            raise ValueError("Payee must have an account first")
        if group_id not in payee_groups:
            raise ValueError("Payee must belong to the group")

        return SettlementRepository(db).create_settlement(group_id, settlement_in)
    finally:
        db.close()


def get_group_settlements(group_id: int):
    db = SessionLocal()
    try:
        return SettlementRepository(db).get_group_settlements(group_id)
    finally:
        db.close()
