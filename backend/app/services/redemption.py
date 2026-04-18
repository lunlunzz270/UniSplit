from datetime import datetime, timedelta, timezone
from ..core.database import SessionLocal
from ..repositories.redemption import RedemptionRepository
from ..repositories.users import UserRepository
from ..models.redemption_codes import CodeCategory


def _user_snapshot(user):
    if not user:
        return {
            "balance": 0.0,
            "is_vip": False,
            "vip_expiry": None,
        }
    return {
        "balance": float(user.balance) if user.balance is not None else 0.0,
        "is_vip": user.is_vip,
        "vip_expiry": user.vip_expiry.isoformat() if user and user.vip_expiry else None,
    }

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
            user_repo.update_balance(user_id, float(db_code.value))
            user = user_repo.get_user_by_id(user_id)
            return {
                "status": "success",
                "message": f"Successfully recharged ${db_code.value} to your account",
                "category": "CASH",
                "value": float(db_code.value),
                **_user_snapshot(user),
            }

        elif db_code.category == CodeCategory.VIP:
            user = user_repo.get_user_by_id(user_id)
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            current_expiry = user.vip_expiry if (user.vip_expiry and user.vip_expiry > now) else now
            new_expiry = current_expiry + timedelta(days=int(db_code.value))
            user_repo.update_vip_status(user_id, True, new_expiry)
            updated_user = user_repo.get_user_by_id(user_id)
            return {
                "status": "success",
                "message": f"Successfully upgraded membership for {int(db_code.value)} days",
                "category": "VIP",
                "value": int(db_code.value),
                **_user_snapshot(updated_user),
            }
    finally:
        db.close()

def buy_membership_with_balance(user_id: int, plan_type: str):
    """Buy membership using current account balance."""
    plans = {
        "monthly": {"price": 9.99, "days": 30},
        "yearly": {"price": 89.99, "days": 365}
    }
    if plan_type not in plans:
        raise ValueError("Invalid membership plan")
    
    plan = plans[plan_type]
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        if float(user.balance) < plan["price"]:
            raise ValueError(f"Insufficient balance. Plan costs ${plan['price']}")
            
        # Deduct balance
        user_repo.update_balance(user_id, -plan["price"])
        
        # Extend VIP
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        current_expiry = user.vip_expiry if (user.vip_expiry and user.vip_expiry > now) else now
        new_expiry = current_expiry + timedelta(days=plan["days"])
        user_repo.update_vip_status(user_id, True, new_expiry)
        updated_user = user_repo.get_user_by_id(user_id)

        return {
            "status": "success",
            "message": f"Plan {plan_type} activated successfully!",
            "plan": plan_type,
            "price": plan["price"],
            "days": plan["days"],
            **_user_snapshot(updated_user),
        }
    finally:
        db.close()
