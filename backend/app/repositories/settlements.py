from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..models.expenses import Settlement, ExpenseParticipant
from ..models.users import User
from ..schemas.settlements import SettlementCreate
from .activity_logs import ActivityLogRepository


class SettlementRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_settlement(self, group_id: int, settlement_in: SettlementCreate) -> Settlement:
        """Record a new repayment transaction between users with atomic balance transfer."""
        try:
            # 1. Lock the users for update to prevent concurrent race conditions
            payer = self.db.query(User).with_for_update().filter(User.id == settlement_in.payer_id).first()
            payee = self.db.query(User).with_for_update().filter(User.id == settlement_in.payee_id).first()

            if not payer or not payee:
                raise ValueError("Payer or Payee not found")

            # Initialize balance if None
            from decimal import Decimal
            if payer.balance is None:
                payer.balance = Decimal("0.00")
            if payee.balance is None:
                payee.balance = Decimal("0.00")

            # 2. Check sufficient balance
            if payer.balance < settlement_in.amount:
                raise ValueError("Insufficient balance. Please recharge your wallet.")

            # 3. Perform atomic transfer
            payer.balance -= settlement_in.amount
            payee.balance += settlement_in.amount

            # 4. Update the expense participant's status to reflect the payment
            participant = self.db.query(ExpenseParticipant).filter(
                ExpenseParticipant.expense_id == settlement_in.expense_id,
                ExpenseParticipant.user_id == settlement_in.payer_id
            ).first()

            if participant:
                participant.is_settled = True
                participant.status = "paid"

            # 5. Create the settlement record
            db_settlement = Settlement(
                group_id=group_id,
                expense_id=settlement_in.expense_id,
                payer_id=settlement_in.payer_id,
                payee_id=settlement_in.payee_id,
                amount=settlement_in.amount,
                status="paid",
                settled_at=datetime.now(timezone.utc).replace(tzinfo=None),
                note=settlement_in.note,
            )
            self.db.add(db_settlement)
            self.db.flush()

            # 6. Log the transaction for admin audit and group history
            ActivityLogRepository(self.db).create_log(
                group_id=group_id,
                user_id=settlement_in.payer_id,
                action_type="settlement_recorded",
                description=f"Paid {settlement_in.amount} to {payee.full_name}",
                ref_id=db_settlement.id,
            )

            # 7. Commit everything together
            self.db.commit()
            self.db.refresh(db_settlement)
            return db_settlement

        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
        except ValueError:
            self.db.rollback()
            raise

    def get_group_settlements(self, group_id: int):
        """Fetch all repayment history for a specific group."""
        return self.db.query(Settlement).filter(Settlement.group_id == group_id).order_by(
            Settlement.settled_at.desc()).all()
