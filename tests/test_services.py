from bcrypt import hashpw, gensalt
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.services.auth import create_user, get_user_by_email, verify_password
from backend.app.services.expenses import record_expense
from backend.app.repositories.users import UserRepository
from backend.app.schemas.users import UserCreate
from backend.app.models.expenses import Expense


def _build_test_sessionmaker():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    import backend.app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    return Session


def test_verify_password_round_trip():
    password = "SecurePassword123!"
    hashed = hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")

    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_auth_service_create_and_lookup_user(monkeypatch):
    session_factory = _build_test_sessionmaker()
    monkeypatch.setattr("backend.app.services.auth.SessionLocal", session_factory)

    user = create_user("Service User", "service@example.com", "test123")
    found = get_user_by_email("service@example.com")

    assert user.id is not None
    assert user.full_name == "Service User"
    assert found is not None
    assert found.email == "service@example.com"


def test_record_expense_creates_group_and_splits(monkeypatch):
    session_factory = _build_test_sessionmaker()
    monkeypatch.setattr("backend.app.services.expenses.SessionLocal", session_factory)

    db = session_factory()
    repo = UserRepository(db)
    payer = repo.create_user(UserCreate(full_name="Payer", email="payer@example.com", password="pwd"))
    participant = repo.create_user(UserCreate(full_name="Participant", email="participant@example.com", password="pwd"))

    expense = record_expense(
        group_name="Sprint4 Trip",
        description="Taxi",
        amount=Decimal("10.00"),
        category="Travel",
        payer_email=payer.email,
        participant_emails=[payer.email, participant.email],
    )

    assert expense.id is not None

    verify_db = session_factory()
    saved_expense = verify_db.query(Expense).filter_by(id=expense.id).first()
    assert saved_expense is not None
    assert saved_expense.description == "Taxi"
    assert saved_expense.group.name == "Sprint4 Trip"
    assert len(saved_expense.participants) == 2
    verify_db.close()

    db.close()


def test_record_expense_deduplicates_participants(monkeypatch):
    session_factory = _build_test_sessionmaker()
    monkeypatch.setattr("backend.app.services.expenses.SessionLocal", session_factory)

    db = session_factory()
    repo = UserRepository(db)
    payer = repo.create_user(UserCreate(full_name="Payer", email="payer2@example.com", password="pwd"))
    teammate = repo.create_user(UserCreate(full_name="Teammate", email="teammate2@example.com", password="pwd"))

    expense = record_expense(
        group_name="Sprint5 Dinner",
        description="Pizza",
        amount=Decimal("30.00"),
        category="Food",
        payer_email=payer.email,
        participant_emails=[payer.email, teammate.email, teammate.email],
    )

    verify_db = session_factory()
    saved_expense = verify_db.query(Expense).filter_by(id=expense.id).first()
    assert saved_expense is not None
    assert len(saved_expense.participants) == 2
    verify_db.close()
    db.close()
