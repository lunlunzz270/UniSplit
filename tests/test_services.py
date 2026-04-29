from bcrypt import hashpw, gensalt
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.services.auth import (
    create_session_for_user,
    create_user,
    get_current_user_from_token,
    get_user_by_email,
    logout_session,
    verify_password,
)
from backend.app.services.groups import can_manage_group, join_group, leave_group
from backend.app.services.expenses import record_expense
from backend.app.repositories.users import UserRepository
from backend.app.repositories.groups import GroupRepository
from backend.app.schemas.groups import GroupCreate
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


def test_auth_service_session_lifecycle(monkeypatch):
    session_factory = _build_test_sessionmaker()
    monkeypatch.setattr("backend.app.services.auth.SessionLocal", session_factory)

    user = create_user("Session User", "session@example.com", "secret")
    session = create_session_for_user(user.id)

    current = get_current_user_from_token(session.token)
    assert current is not None
    current_user, current_session = current
    assert current_user.email == "session@example.com"
    assert current_session.token == session.token

    assert logout_session(session.token) is True
    assert get_current_user_from_token(session.token) is None


def test_group_service_join_and_leave(monkeypatch):
    session_factory = _build_test_sessionmaker()
    monkeypatch.setattr("backend.app.services.groups.SessionLocal", session_factory)

    db = session_factory()
    user_repo = UserRepository(db)
    group_repo = GroupRepository(db)
    creator = user_repo.create_user(UserCreate(full_name="Group Creator", email="group.creator@example.com", password="pwd"))
    member = user_repo.create_user(UserCreate(full_name="Group Member", email="group.member@example.com", password="pwd"))
    group = group_repo.create_group(GroupCreate(name="Service Group"), creator.id)
    group_id = group.id
    creator_id = creator.id
    member_id = member.id
    db.close()

    assert can_manage_group(group_id, creator_id) is True
    joined_member, created = join_group(group_id, member_id)
    assert created is True
    assert joined_member["user_id"] == member_id

    removed = leave_group(group_id, member_id)
    assert removed["user_id"] == member_id


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
    # Logic: 2 emails (payer + participant) -> Only 1 debt record (the participant)
    assert len(saved_expense.participants) == 1
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
    # [payer, teammate, teammate] -> only 1 participant record (the teammate)
    assert len(saved_expense.participants) == 1
    verify_db.close()
    db.close()


def test_expense_precision_splitting(monkeypatch):
    session_factory = _build_test_sessionmaker()
    monkeypatch.setattr("backend.app.services.expenses.SessionLocal", session_factory)

    db = session_factory()
    repo = UserRepository(db)
    payer = repo.create_user(UserCreate(full_name="Payer", email="payer_prec@example.com", password="pwd"))
    p1 = repo.create_user(UserCreate(full_name="P1", email="p1@example.com", password="pwd"))
    p2 = repo.create_user(UserCreate(full_name="P2", email="p2@example.com", password="pwd"))

    # $10.00 split by 3 people = 3.33, 3.33, 3.34
    expense = record_expense(
        group_name="Precision Test",
        description="Uneven Split",
        amount=Decimal("10.00"),
        category="Food",
        payer_email=payer.email,
        participant_emails=[payer.email, p1.email, p2.email],
    )

    verify_db = session_factory()
    saved = verify_db.query(Expense).filter_by(id=expense.id).first()
    # Payer is excluded from DB participant records, so we should have 2 records (p1, p2)
    # The shares should be 3.33 and 3.34 (the remainder goes to the last person in participant_emails list)
    shares = sorted([float(p.share) for p in saved.participants])
    assert shares == [3.33, 3.34]
    assert sum(shares) + 3.33 == 10.00 # total includes the payer's implied share
    verify_db.close()
    db.close()


def test_admin_financial_isolation(monkeypatch):
    session_factory = _build_test_sessionmaker()
    monkeypatch.setattr("backend.app.services.expenses.SessionLocal", session_factory)

    db = session_factory()
    repo = UserRepository(db)
    admin = repo.create_user(UserCreate(full_name="Admin", email="admin@unisplit.com", password="pwd"), is_admin=True)
    user = repo.create_user(UserCreate(full_name="User", email="user@example.com", password="pwd"))

    # Case 1: Admin cannot pay
    import pytest
    with pytest.raises(ValueError, match="Administrative users are not allowed"):
        record_expense(
            group_name="Admin Group",
            description="Forbidden",
            amount=Decimal("10.00"),
            category="Test",
            payer_email=admin.email,
            participant_emails=[admin.email, user.email],
        )

    # Case 2: Admin cannot be a participant
    with pytest.raises(ValueError, match="is an administrator and cannot be added"):
        record_expense(
            group_name="Admin Group",
            description="Forbidden",
            amount=Decimal("10.00"),
            category="Test",
            payer_email=user.email,
            participant_emails=[user.email, admin.email],
        )
    db.close()


def test_auto_settlement_heartbeat(monkeypatch):
    # This tests the "Auto-payment heartbeat" in get_current_user_from_token
    session_factory = _build_test_sessionmaker()
    monkeypatch.setattr("backend.app.services.auth.SessionLocal", session_factory)
    monkeypatch.setattr("backend.app.services.expenses.SessionLocal", session_factory)
    monkeypatch.setattr("backend.app.services.settlements.SessionLocal", session_factory)

    db = session_factory()
    repo = UserRepository(db)
    payer = repo.create_user(UserCreate(full_name="Payer", email="payer_auto@example.com", password="pwd"))
    debtor = repo.create_user(UserCreate(full_name="Debtor", email="debtor_auto@example.com", password="pwd"))
    
    # Give debtor some balance to pay with
    debtor.balance = Decimal("50.00")
    db.commit()

    # Create an expense
    expense = record_expense(
        group_name="Auto Group",
        description="Timed Bill",
        amount=Decimal("20.00"),
        category="Test",
        payer_email=payer.email,
        participant_emails=[payer.email, debtor.email],
    )

    # Manually backdate the expense and split in DB to > 24h ago
    from datetime import datetime, timedelta
    old_time = datetime.now() - timedelta(hours=25)
    
    from backend.app.models.expenses import ExpenseParticipant
    db.query(Expense).filter_by(id=expense.id).update({"created_at": old_time})
    db.query(ExpenseParticipant).filter_by(expense_id=expense.id).update({"status": "accepted"})
    db.commit()

    # Trigger heartbeat via auth service
    from backend.app.services.auth import create_session_for_user, get_current_user_from_token
    session = create_session_for_user(debtor.id)
    
    # This call should trigger auto_process_payments(debtor.id)
    get_current_user_from_token(session.token)

    # Verify settlement happened
    db.expire_all()
    debtor_after = repo.get_user_by_id(debtor.id)
    payer_after = repo.get_user_by_id(payer.id)
    split = db.query(ExpenseParticipant).filter_by(expense_id=expense.id).first()

    assert debtor_after.balance == Decimal("40.00") # 50 - 10
    assert payer_after.balance == Decimal("10.00")  # 0 + 10
    assert split.is_settled is True
    db.close()


def test_currency_service_fallback_and_conversion():
    from backend.app.integrations.currency import CurrencyService
    service = CurrencyService(cache_ttl_seconds=10)
    
    # Test fallback retrieval
    rates = service.get_rates(base="USD")
    assert rates["base"] == "USD"
    assert "EUR" in rates["rates"]
    assert "CNY" in rates["rates"]

    # Test conversion accuracy
    amount = Decimal("100.00")
    converted_self = service.convert(amount, "USD", "USD")
    assert converted_self == Decimal("100.00")

    converted_eur = service.convert(amount, "USD", "EUR")
    assert converted_eur > Decimal("0.00")


def test_reconcile_ledger_balances_no_crash(monkeypatch):
    import logging
    from backend.main import reconcile_ledger_balances
    session_factory = _build_test_sessionmaker()
    db = session_factory()
    test_logger = logging.getLogger("test_security")
    
    # Should run smoothly on empty or populated test database
    reconcile_ledger_balances(db, test_logger)
    db.close()

