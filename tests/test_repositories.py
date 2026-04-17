import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the declarative Base, ORM Models, and Pydantic Schemas
from backend.app.core.database import Base
from backend.app.models.users import User
from backend.app.models.groups import Group, GroupMember
from backend.app.models.expenses import Expense, ExpenseParticipant, Settlement

from backend.app.schemas.users import UserCreate
from backend.app.schemas.groups import GroupCreate
from backend.app.schemas.expenses import ExpenseCreate, ExpenseParticipantBase
from backend.app.schemas.settlements import SettlementCreate

# Import the Repositories to be tested
from backend.app.repositories.users import UserRepository
from backend.app.repositories.groups import GroupRepository
from backend.app.repositories.expenses import ExpenseRepository
from backend.app.repositories.settlements import SettlementRepository

# ==========================================
# 1. Database Configuration for Testing (Pytest Fixture)
# ==========================================

# Configure an in-memory SQLite database specifically for testing purposes.
# Using ':memory:' ensures that tests run incredibly fast, remain completely isolated
# from your production/development MySQL database, and leave no residual files on the disk.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Setup and teardown mechanism for the database session.
    This fixture is executed before and after EACH test function to guarantee a completely clean state.

    Setup phase: Creates all defined tables in the in-memory SQLite database and yields the active session.
    Teardown phase: Closes the session and drops all tables to prevent data leakage between tests.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


# ==========================================
# 2. UserRepository Tests
# ==========================================

def test_create_and_get_user(db_session):
    """
    Verify that a user can be successfully created and subsequently retrieved
    using both their email address and their unique database ID.
    """
    repo = UserRepository(db_session)

    # Define the payload using the Pydantic Schema
    user_data = UserCreate(full_name="Alice Smith", email="alice@duke.edu", password="hashed_pwd")

    # 1. Test user creation
    # The repository should handle the insertion, commit the transaction, and refresh the object to fetch the auto-generated ID.
    created_user = repo.create_user(user_data)
    assert created_user.id is not None, "Database should have auto-generated an integer ID"
    assert created_user.full_name == "Alice Smith"
    assert created_user.email == "alice@duke.edu"

    # 2. Test fetching the user by their email address (used frequently during the login process)
    fetched_user = repo.get_user_by_email("alice@duke.edu")
    assert fetched_user is not None, "User should be locatable via their registered email"
    assert fetched_user.id == created_user.id

    # 3. Test fetching the user by their primary key (ID)
    fetched_by_id = repo.get_user_by_id(created_user.id)
    assert fetched_by_id is not None
    assert fetched_by_id.email == "alice@duke.edu"


# ==========================================
# 3. GroupRepository Tests
# ==========================================

def test_create_group_and_auto_admin(db_session):
    """
    Verify the group creation process, specifically testing the critical business logic:
    When a user creates a group, they must automatically be added to the 'GroupMember'
    bridge table and be assigned the role of 'ADMIN'.
    """
    user_repo = UserRepository(db_session)
    group_repo = GroupRepository(db_session)

    # Prerequisite: Create a mock user to act as the group creator
    user = user_repo.create_user(UserCreate(full_name="Bob", email="bob@duke.edu", password="pwd"))

    # 1. Test group creation
    group_data = GroupCreate(name="Spring Break Trip", description="Miami 2026")
    created_group = group_repo.create_group(group_data, creator_id=user.id)

    assert created_group.id is not None
    assert created_group.name == "Spring Break Trip"
    assert created_group.created_by == user.id

    # 2. Verify that the creator was properly added to the group via the SQL JOIN query
    user_groups = group_repo.get_user_groups(user.id)
    assert len(user_groups) == 1, "The user should belong to exactly one group"
    assert user_groups[0].name == "Spring Break Trip"

    # 3. Core Verification: Query the bridge table directly to ensure the correct 'ADMIN' role was applied
    member_record = db_session.query(GroupMember).filter_by(group_id=created_group.id, user_id=user.id).first()
    assert member_record is not None, "A record must exist in the GroupMember bridge table"
    assert member_record.role == "ADMIN", "The creator must be assigned the ADMIN role automatically"


def test_add_user_to_group_is_idempotent_and_updates_role(db_session):
    user_repo = UserRepository(db_session)
    group_repo = GroupRepository(db_session)

    user = user_repo.create_user(UserCreate(full_name="Role User", email="role@test.com", password="pwd"))
    group = group_repo.create_group(GroupCreate(name="Role Group"), creator_id=user.id)

    member = group_repo.add_user_to_group(group.id, user.id, role="MEMBER")
    updated = group_repo.add_user_to_group(group.id, user.id, role="ADMIN")

    assert member.id == updated.id
    assert updated.role == "ADMIN"


# ==========================================
# 4. ExpenseRepository Tests (Critical Financial Logic)
# ==========================================

def test_create_expense_with_splits_transaction(db_session):
    """
    Verify the atomic transaction of creating an expense alongside its participant splits.
    This test ensures that the main Expense record and the multiple ExpenseParticipant
    records are correctly linked via foreign keys and saved together successfully.
    """
    user_repo = UserRepository(db_session)
    group_repo = GroupRepository(db_session)
    expense_repo = ExpenseRepository(db_session)

    # Prerequisite: Create two users and a shared group
    u1 = user_repo.create_user(UserCreate(full_name="User1", email="u1@test.com", password="123"))
    u2 = user_repo.create_user(UserCreate(full_name="User2", email="u2@test.com", password="123"))
    group = group_repo.create_group(GroupCreate(name="Dinner Group"), creator_id=u1.id)

    # Add the second user to the group so both are valid participants
    group_repo.add_user_to_group(group_id=group.id, user_id=u2.id)

    # Prepare the payload: A $100 expense paid by User1, split equally between User1 and User2
    expense_data = ExpenseCreate(
        amount=Decimal("100.00"),
        category="Dining",
        description="Pizza Night",
        paid_by=u1.id,
        participants=[
            ExpenseParticipantBase(user_id=u1.id, share=Decimal("50.00")),
            ExpenseParticipantBase(user_id=u2.id, share=Decimal("50.00"))
        ]
    )

    # 1. Trigger the core transaction method
    created_expense = expense_repo.create_expense_with_splits(group_id=group.id, expense_in=expense_data)

    # 2. Verify the main expense record was created successfully
    assert created_expense.id is not None
    assert created_expense.amount == Decimal("100.00")

    # 3. Verify the cascading split records:
    # Query the database to ensure exactly 2 ExpenseParticipant records are linked to the new expense.
    participants = db_session.query(ExpenseParticipant).filter_by(expense_id=created_expense.id).all()
    assert len(participants) == 2, "There should be exactly two participant records generated"

    # 4. Verify financial accuracy: Ensure the specific split amounts correspond correctly to the designated users
    shares = {p.user_id: p.share for p in participants}
    assert shares[u1.id] == Decimal("50.00")
    assert shares[u2.id] == Decimal("50.00")

    # 5. Verify the group expense history retrieval function
    group_expenses = expense_repo.get_group_expenses(group.id)
    assert len(group_expenses) == 1
    assert group_expenses[0].description == "Pizza Night"


def test_create_expense_with_splits_rejects_outsider_participant(db_session):
    user_repo = UserRepository(db_session)
    group_repo = GroupRepository(db_session)
    expense_repo = ExpenseRepository(db_session)

    payer = user_repo.create_user(UserCreate(full_name="Payer", email="payer3@test.com", password="123"))
    insider = user_repo.create_user(UserCreate(full_name="Insider", email="insider3@test.com", password="123"))
    outsider = user_repo.create_user(UserCreate(full_name="Outsider", email="outsider3@test.com", password="123"))
    group = group_repo.create_group(GroupCreate(name="Validation Group"), creator_id=payer.id)
    group_repo.add_user_to_group(group.id, insider.id)

    expense_data = ExpenseCreate(
        amount=Decimal("20.00"),
        category="Dining",
        description="Lunch",
        paid_by=payer.id,
        participants=[
            ExpenseParticipantBase(user_id=insider.id, share=Decimal("10.00")),
            ExpenseParticipantBase(user_id=outsider.id, share=Decimal("10.00")),
        ],
    )

    with pytest.raises(ValueError, match="All participants must belong to the group"):
        expense_repo.create_expense_with_splits(group.id, expense_data)


# ==========================================
# 5. SettlementRepository Tests
# ==========================================

def test_create_and_get_settlements(db_session):
    """
    Verify that repayment transactions (settlements) between users within a specific
    group are correctly recorded and can be retrieved as historical data.
    """
    user_repo = UserRepository(db_session)
    group_repo = GroupRepository(db_session)
    settle_repo = SettlementRepository(db_session)

    # Prerequisite: Create the payer, the payee, and the group context
    payer = user_repo.create_user(UserCreate(full_name="Payer", email="payer@test.com", password="123"))
    # Manual balance top-up for test
    user_repo.update_balance(payer.id, 100.00)
    
    payee = user_repo.create_user(UserCreate(full_name="Payee", email="payee@test.com", password="123"))
    group = group_repo.create_group(GroupCreate(name="Roommates"), creator_id=payee.id)

    # Prepare the payload representing a user clicking "Settle Up"
    settlement_data = SettlementCreate(
        expense_id=1, # Mock ID
        payer_id=payer.id,
        payee_id=payee.id,
        amount=Decimal("25.50"),
        note="Venmo for utilities"
    )
    # 1. Create the settlement record
    created_settlement = settle_repo.create_settlement(group.id, settlement_data)

    assert created_settlement.id is not None
    assert created_settlement.amount == Decimal("25.50")
    assert created_settlement.note == "Venmo for utilities"

    # 2. Verify that the settlement appears in the group's repayment history
    history = settle_repo.get_group_settlements(group.id)
    assert len(history) == 1
    assert history[0].payer_id == payer.id
    assert history[0].payee_id == payee.id


def test_settlement_history_empty_for_new_group(db_session):
    user_repo = UserRepository(db_session)
    group_repo = GroupRepository(db_session)
    settle_repo = SettlementRepository(db_session)

    payer = user_repo.create_user(UserCreate(full_name="Payer", email="payer4@test.com", password="123"))
    group = group_repo.create_group(GroupCreate(name="Empty Group"), creator_id=payer.id)

    history = settle_repo.get_group_settlements(group.id)
    assert history == []
