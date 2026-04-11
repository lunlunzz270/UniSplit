from sqlalchemy.orm import Session
from ..models.expenses import Settlement
from ..schemas.settlements import SettlementCreate
from .activity_logs import ActivityLogRepository


class SettlementRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_settlement(self, group_id: int, settlement_in: SettlementCreate) -> Settlement:
        """Record a new repayment transaction between users."""
        db_settlement = Settlement(
            group_id=group_id,
            payer_id=settlement_in.payer_id,
            payee_id=settlement_in.payee_id,
            amount=settlement_in.amount,
            note=settlement_in.note,
        )
        self.db.add(db_settlement)
        self.db.flush()

        ActivityLogRepository(self.db).create_log(
            group_id=group_id,
            user_id=settlement_in.payer_id,
            action_type="settlement_recorded",
            description=f"Settlement of {settlement_in.amount} recorded",
            ref_id=db_settlement.id,
        )

        self.db.commit()
        self.db.refresh(db_settlement)
        return db_settlement

    def get_group_settlements(self, group_id: int):
        """Fetch all repayment history for a specific group."""
        return self.db.query(Settlement).filter(Settlement.group_id == group_id).order_by(
            Settlement.settled_at.desc()).all()
