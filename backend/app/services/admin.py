from ..core.database import SessionLocal
from ..repositories.users import UserRepository


def list_users():
    db = SessionLocal()
    try:
        return UserRepository(db).list_users()
    finally:
        db.close()


def set_user_active(user_id: int, is_active: bool):
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        return user_repo.set_user_active(user_id, is_active)
    finally:
        db.close()
