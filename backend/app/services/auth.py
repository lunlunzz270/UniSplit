from datetime import datetime, timedelta
from secrets import token_urlsafe
from uuid import uuid4

from bcrypt import checkpw, gensalt, hashpw

from ..core.database import SessionLocal
from ..repositories.users import UserRepository
from ..schemas.users import UserCreate

SESSION_TTL_DAYS = 7


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


def create_session_for_user(user_id: int, ttl_days: int = SESSION_TTL_DAYS):
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user_repo.delete_sessions_for_user(user_id)
        session = user_repo.create_session(
            user_id=user_id,
            token=token_urlsafe(32),
            expires_at=datetime.now() + timedelta(days=ttl_days),
            session_id=uuid4().hex,
        )
        return session
    finally:
        db.close()


def get_current_user_from_token(session_token: str):
    if not session_token:
        return None

    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        session = user_repo.get_session_by_token(session_token)
        if not session:
            return None

        if session.expires_at <= datetime.now():
            user_repo.delete_session_by_token(session_token)
            return None

        user = user_repo.get_user_by_id(session.user_id)
        if not user or not user.is_active:
            return None

        return user, session
    finally:
        db.close()


def logout_session(session_token: str) -> bool:
    if not session_token:
        return False

    db = SessionLocal()
    try:
        return UserRepository(db).delete_session_by_token(session_token)
    finally:
        db.close()


def serialize_session(session):
    return {
        "id": session.id,
        "token": session.token,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


def serialize_user(user, session=None):
    payload = {
        "id": user.id,
        "name": user.full_name,
        "email": user.email,
    }
    if session is not None:
        payload["session"] = serialize_session(session)
        payload["session_token"] = session.token
        payload["session_expires_at"] = session.expires_at.isoformat() if session.expires_at else None
    return payload
