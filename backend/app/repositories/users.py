from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from ..models.users import Session as UserSession
from ..models.users import User
from ..schemas.users import UserCreate

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        """Fetch a user by email, used for login validation and registration duplication checks."""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> User | None:
        """Fetch a single user by their ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_in: UserCreate, is_admin: bool = False) -> User:
        """Create and save a new ORM User object from Schema data."""
        # Note: user_in.password should already be hashed by the Service layer before reaching here
        db_user = User(
            full_name=user_in.full_name,
            email=str(user_in.email),
            password=user_in.password,
            is_admin=is_admin
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user) # Refresh to get the database-generated auto-increment ID
        return db_user

    def create_session(self, user_id: int, token: str, expires_at: datetime, session_id: str | None = None) -> UserSession:
        db_session = UserSession(
            id=session_id or uuid4().hex,
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def get_session_by_token(self, token: str) -> UserSession | None:
        return self.db.query(UserSession).filter(UserSession.token == token).first()

    def delete_session_by_token(self, token: str) -> bool:
        session = self.get_session_by_token(token)
        if not session:
            return False
        self.db.delete(session)
        self.db.commit()
        return True

    def delete_sessions_for_user(self, user_id: int) -> int:
        sessions = self.db.query(UserSession).filter(UserSession.user_id == user_id).all()
        count = len(sessions)
        for session in sessions:
            self.db.delete(session)
        if count:
            self.db.commit()
        return count
