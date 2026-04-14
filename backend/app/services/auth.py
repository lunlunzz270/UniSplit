from datetime import datetime, timedelta
from bcrypt import checkpw, gensalt, hashpw
from ..core.database import SessionLocal
from ..repositories.users import UserRepository
from ..schemas.users import UserCreate
from ..core.auth import create_access_token, ADMIN_DOMAIN
from ..models.users import Session, User

def get_user_by_email(email: str):
    db = SessionLocal()
    try:
        return UserRepository(db).get_user_by_email(email)
    finally:
        db.close()


def create_user(name: str, email: str, password: str):
    """
    Create a new user. Automatically set is_admin status based on the email domain.
    """
    db = SessionLocal()
    try:
        is_admin = email.lower().endswith(ADMIN_DOMAIN)
        hashed_password = hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")
        user = UserRepository(db).create_user(
            UserCreate(full_name=name, email=email, password=hashed_password),
            is_admin=is_admin
        )
        return user
    finally:
        db.close()


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def authenticate_user(email: str, password: str):
    """
    Validates credentials and returns a Token along with user details and admin status.
    """
    user = get_user_by_email(email)
    if user and verify_password(password, user.password):
        token = create_access_token(user.id, user.email)
        return {
            "token": token,
            "is_admin": user.is_admin,
            "user": {
                "id": user.id,
                "name": user.full_name,
                "email": user.email
            }
        }
    return None

def create_session_for_user(user_id: int):
    """
    Create a new database session for the user and generate a JWT token.
    """
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        user = repo.get_user_by_id(user_id)
        if not user:
            return None
        
        token = create_access_token(user.id, user.email)
        # Session expires in 1 day
        expires_at = datetime.utcnow() + timedelta(days=1)
        session = repo.create_session(user_id, token, expires_at)
        return session
    finally:
        db.close()

def get_current_user_from_token(token: str):
    """
    Validate session token and return (User, Session) tuple if valid.
    """
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        session = repo.get_session_by_token(token)
        if not session:
            return None
        
        # Check expiration
        if session.expires_at < datetime.utcnow():
            repo.delete_session_by_token(token)
            return None
            
        user = repo.get_user_by_id(session.user_id)
        if not user:
            return None
            
        return user, session
    finally:
        db.close()

def logout_session(token: str):
    """
    Remove the session associated with the token.
    """
    db = SessionLocal()
    try:
        return UserRepository(db).delete_session_by_token(token)
    finally:
        db.close()

def serialize_user(user: User, session: Session = None):
    """
    Format user and session data for API responses.
    """
    return {
        "id": user.id,
        "name": user.full_name,
        "email": user.email,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "balance": float(user.balance),
        "is_vip": user.is_vip,
        "vip_expiry": user.vip_expiry.isoformat() if user.vip_expiry else None,
        "session": {
            "token": session.token,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None
        } if session else None
    }
