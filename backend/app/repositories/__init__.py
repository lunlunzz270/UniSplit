from .users import UserRepository
from .groups import GroupRepository
from .expenses import ExpenseRepository
from .settlements import SettlementRepository

from bcrypt import checkpw, gensalt, hashpw

from ..core.database import SessionLocal
from ..schemas.users import UserCreate


def get_user_by_email(email: str):
    db = SessionLocal()
    try:
        return UserRepository(db).get_user_by_email(email)
    finally:
        db.close()


def create_user(name: str, email: str, password: str):
    db = SessionLocal()
    try:
        hashed_password = hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")
        user = UserRepository(db).create_user(
            UserCreate(full_name=name, email=email, password=hashed_password)
        )
        return user
    finally:
        db.close()


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False
