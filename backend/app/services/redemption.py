from datetime import datetime, timedelta
from ..core.database import SessionLocal
from ..repositories.redemption import RedemptionRepository
from ..repositories.users import UserRepository
from ..models.redemption_codes import CodeCategory

def redeem_code(user_id: int, code_str: str):
    db = SessionLocal()
    try:
        redemption_repo = RedemptionRepository(db)
        user_repo = UserRepository(db)

        db_code = redemption_repo.get_code(code_str)
        if not db_code:
            raise ValueError("Invalid redemption code")
        if db_code.is_used:
            raise ValueError("This code has already been used")

        # Atomic redemption process
        redemption_repo.redeem_code(db_code.id, user_id)

        if db_code.category == CodeCategory.CASH:
            # Add balance to user
            user_repo.update_balance(user_id, float(db_code.value))
            return {"status": "success", "message": f"Successfully recharged {db_code.value} to your account"}

        elif db_code.category == CodeCategory.VIP:
            # Upgrade membership
            user = user_repo.get_user_by_id(user_id)
            current_expiry = user.vip_expiry or datetime.now()
            new_expiry = max(current_expiry, datetime.now()) + timedelta(days=int(db_code.value))
            user_repo.update_vip_status(user_id, True, new_expiry)
            return {"status": "success", "message": f"Successfully upgraded membership for {int(db_code.value)} days"}

    finally:
        db.close()
