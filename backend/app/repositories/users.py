from sqlalchemy.orm import Session
from backend.app.models.users import User
from backend.app.schemas.users import UserCreate

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        """Fetch a user by email, used for login validation and registration duplication checks."""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> User | None:
        """Fetch a single user by their ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_in: UserCreate) -> User:
        """Create and save a new ORM User object from Schema data."""
        # Note: user_in.password should already be hashed by the Service layer before reaching here
        db_user = User(
            full_name=user_in.full_name,
            email=str(user_in.email),
            password=user_in.password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user) # Refresh to get the database-generated auto-increment ID
        return db_user