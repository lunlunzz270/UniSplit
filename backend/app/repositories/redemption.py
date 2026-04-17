from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models.redemption_codes import RedemptionCode, CodeCategory

class RedemptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_code(self, code: str) -> RedemptionCode | None:
        return self.db.query(RedemptionCode).filter(RedemptionCode.code == code).first()

    def redeem_code(self, code_id: int, user_id: int) -> RedemptionCode | None:
        db_code = self.db.query(RedemptionCode).filter(RedemptionCode.id == code_id).first()
        if db_code and not db_code.is_used:
            db_code.is_used = True
            db_code.used_by_id = user_id
            db_code.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.db.commit()
            self.db.refresh(db_code)
        return db_code

    def create_code(self, code: str, category: CodeCategory, value: float) -> RedemptionCode:
        db_code = RedemptionCode(
            code=code,
            category=category,
            value=value
        )
        self.db.add(db_code)
        self.db.commit()
        self.db.refresh(db_code)
        return db_code
