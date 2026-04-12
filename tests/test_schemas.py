import pytest
from pydantic import ValidationError
from decimal import Decimal
from backend.app.schemas.users import RegisterRequest, UserCreate, LoginRequest, UserResponse
from backend.app.schemas.groups import GroupCreate, GroupRead
from backend.app.schemas.expenses import ExpenseCreate, ExpenseParticipantBase, ExpenseRead, ExpenseParticipantRead
from backend.app.schemas.settlements import SettlementCreate, SettlementRead


# ==========================================
# Test Suite: User & Authentication Schemas
# ==========================================

def test_register_request_valid_data():
    """Test successful creation of a RegisterRequest with valid data."""
    valid_data = {
        "name": "John Doe",
        "email": "john.doe@duke.edu",
        "password": "SecurePassword123!"
    }
    user_req = RegisterRequest(**valid_data)

    assert user_req.name == "John Doe"
    assert user_req.email == "john.doe@duke.edu"
    assert user_req.password == "SecurePassword123!"


def test_register_request_invalid_email():
    """Test that an invalid email format raises a ValidationError."""
    invalid_data = {
        "name": "John Doe",
        "email": "not-an-email",  # Invalid email format
        "password": "SecurePassword123!"
    }

    with pytest.raises(ValidationError) as excinfo:
        RegisterRequest(**invalid_data)

    assert "email" in str(excinfo.value).lower()


def test_user_create_missing_required_field():
    """Test that missing a required field (e.g., password) raises an error."""
    invalid_data = {
        "full_name": "Jane Smith",
        "email": "jane@example.com"
        # Missing 'password'
    }

    with pytest.raises(ValidationError) as excinfo:
        UserCreate(**invalid_data)

    assert "password" in str(excinfo.value)
    assert "Field required" in str(excinfo.value)


def test_login_request_valid():
    """Test LoginRequest validation."""
    valid_data = {"email": "test@duke.edu", "password": "mypassword"}
    login_req = LoginRequest(**valid_data)
    assert login_req.email == "test@duke.edu"
    assert login_req.password == "mypassword"


class MockUserORM:
    """Mock ORM object to test from_attributes conversion."""

    def __init__(self, id, full_name, email, is_active, is_admin=False):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.is_active = is_active
        self.is_admin = is_admin


def test_user_response_from_orm():
    """Test that UserResponse successfully parses an ORM object."""
    mock_db_user = MockUserORM(id=1, full_name="Alice", email="alice@example.com", is_active=True, is_admin=True)
    user_resp = UserResponse.model_validate(mock_db_user)

    assert user_resp.id == 1
    assert user_resp.full_name == "Alice"
    assert user_resp.is_active is True
    assert user_resp.is_admin is True


# ==========================================
# Test Suite: Group Schemas
# ==========================================

def test_group_create_valid():
    """Test valid GroupCreate."""
    group = GroupCreate(name="Spring Break Miami", description="Trip expenses")
    assert group.name == "Spring Break Miami"
    assert group.description == "Trip expenses"

def test_group_create_optional_description():
    """Test GroupCreate with missing optional description."""
    group = GroupCreate(name="Roommates")
    assert group.name == "Roommates"
    assert group.description is None

def test_group_create_missing_name():
    """Test that creating a group without a name fails."""
    with pytest.raises(ValidationError):
        GroupCreate(description="No name group")

class MockGroupORM:
    def __init__(self, id, name, description, created_by):
        self.id = id
        self.name = name
        self.description = description
        self.created_by = created_by

def test_group_read_from_orm():
    """Test GroupRead from_attributes mapping."""
    mock_db_group = MockGroupORM(id=10, name="Apartment 4B", description=None, created_by=1)
    group_read = GroupRead.model_validate(mock_db_group)
    assert group_read.id == 10
    assert group_read.created_by == 1


# ==========================================
# Test Suite: Expense & Split Schemas
# ==========================================

def test_expense_create_valid_data():
    """Test successful creation of an ExpenseCreate model with nested participants."""
    valid_data = {
        "amount": Decimal("150.75"),
        "category": "Groceries",
        "description": "Weekly grocery run",
        "paid_by": 1,
        "participants": [
            {"user_id": 1, "share": Decimal("50.25")},
            {"user_id": 2, "share": Decimal("100.50")}
        ]
    }

    expense = ExpenseCreate(**valid_data)

    assert expense.amount == Decimal("150.75")
    assert expense.category == "Groceries"
    assert len(expense.participants) == 2
    assert expense.participants[0].share == Decimal("50.25")


def test_expense_amount_zero_or_negative():
    """Test that amounts <= 0 are rejected due to the Field(gt=0) constraint."""
    # Test Negative Amount
    with pytest.raises(ValidationError) as excinfo_negative:
        ExpenseCreate(
            amount=Decimal("-10.00"),
            category="Dining",
            paid_by=1,
            participants=[]
        )
    assert "greater than 0" in str(excinfo_negative.value)

    # Test Zero Amount
    with pytest.raises(ValidationError) as excinfo_zero:
        ExpenseCreate(
            amount=Decimal("0.00"),
            category="Dining",
            paid_by=1,
            participants=[]
        )
    assert "greater than 0" in str(excinfo_zero.value)


def test_expense_participant_precision():
    """Test that the Decimal precision correctly parses string financial inputs."""
    participant_data = {
        "user_id": 3,
        "share": "33.33"  # Passing as string, Pydantic should cast to Decimal
    }

    participant = ExpenseParticipantBase(**participant_data)

    assert isinstance(participant.share, Decimal)
    assert participant.share == Decimal("33.33")


def test_expense_missing_participants_list():
    """Test that creating an expense without the participants list fails."""
    invalid_data = {
        "amount": Decimal("50.00"),
        "category": "Travel",
        "paid_by": 2
        # Missing 'participants'
    }

    with pytest.raises(ValidationError) as excinfo:
        ExpenseCreate(**invalid_data)

    assert "participants" in str(excinfo.value)
    assert "Field required" in str(excinfo.value)


class MockExpenseParticipantORM:
    def __init__(self, id, expense_id, user_id, share, is_settled):
        self.id = id
        self.expense_id = expense_id
        self.user_id = user_id
        self.share = share
        self.is_settled = is_settled


class MockExpenseORM:
    def __init__(self, id, group_id, paid_by, amount, category, description, participants):
        self.id = id
        self.group_id = group_id
        self.paid_by = paid_by
        self.amount = amount
        self.category = category
        self.description = description
        self.participants = participants


def test_expense_read_from_orm():
    """Test mapping an ORM expense with nested participants to ExpenseRead."""
    mock_participants = [
        MockExpenseParticipantORM(id=1, expense_id=100, user_id=2, share=Decimal("20.00"), is_settled=False)
    ]
    mock_expense = MockExpenseORM(
        id=100, group_id=5, paid_by=1, amount=Decimal("20.00"),
        category="Transport", description="Uber", participants=mock_participants
    )

    expense_read = ExpenseRead.model_validate(mock_expense)
    assert expense_read.id == 100
    assert expense_read.amount == Decimal("20.00")
    assert len(expense_read.participants) == 1
    assert expense_read.participants[0].is_settled is False


# ==========================================
# Test Suite: Settlement Schemas
# ==========================================

def test_settlement_create_valid():
    """Test valid SettlementCreate input."""
    data = {
        "payer_id": 2,
        "payee_id": 1,
        "amount": Decimal("45.50"),
        "note": "Venmo transfer"
    }
    settlement = SettlementCreate(**data)
    assert settlement.amount == Decimal("45.50")
    assert settlement.note == "Venmo transfer"


def test_settlement_invalid_amount():
    """Test that Settlement amount strictly follows the gt=0 constraint."""
    with pytest.raises(ValidationError):
        SettlementCreate(payer_id=2, payee_id=1, amount=Decimal("0.00"))

    with pytest.raises(ValidationError):
        SettlementCreate(payer_id=2, payee_id=1, amount=Decimal("-5.00"))


class MockSettlementORM:
    def __init__(self, id, group_id, payer_id, payee_id, amount, note):
        self.id = id
        self.group_id = group_id
        self.payer_id = payer_id
        self.payee_id = payee_id
        self.amount = amount
        self.note = note


def test_settlement_read_from_orm():
    """Test SettlementRead from_attributes mapping."""
    mock_settlement = MockSettlementORM(
        id=50, group_id=2, payer_id=3, payee_id=4, amount=Decimal("15.00"), note=None
    )
    settlement_read = SettlementRead.model_validate(mock_settlement)

    assert settlement_read.id == 50
    assert settlement_read.group_id == 2
    assert settlement_read.amount == Decimal("15.00")
    assert settlement_read.note is None